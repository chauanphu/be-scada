from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.Account import Account, Role
from models.Audit import ActionEnum, Audit
from models.unit import Cluster, Unit
from .dependencies import get_current_user, admin_required, required_permission
from schemas import ClusterCreate, ClusterRead, ClusterReadFull, NodeControl, UnitCreate, UnitRead
from database.session import get_db
from mqtt_client import client, COMMAND
from config import PermissionEnum

router = APIRouter(
    prefix='/clusters',
    tags=['clusters'],
)

def isAdmin(current_user: Account, db: Session):
    role_name = db.query(Role).filter(Role.role_id == current_user.role).first().role_name
    if role_name not in ["ADMIN", "SUPERADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view or edit ADMIN or SUPERADMIN roles."
        )
    return current_user

# Get all clusters, only admin users can access this endpoint
@router.get("/", response_model=list[ClusterReadFull], dependencies=[Depends(required_permission([PermissionEnum.MONITOR_SYSTEM]))]
)
def get_clusters(
    db: Session = Depends(get_db)):
    # Join the Cluster and Unit tables to get all the clusters and their units
    clusters = db.query(Cluster).options(
        joinedload(Cluster.units),
        joinedload(Cluster.account)
    ).all()
    return clusters

# Create a new cluster, only admin users can access this endpoint
@router.post("/", response_model=ClusterRead)
def create_cluster(cluster: ClusterCreate, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    new_cluster = Cluster(
    name=cluster.name,
    account_id=cluster.account_id
)
    db.add(new_cluster)
    db.commit()
    db.refresh(new_cluster)

    for unit in cluster.units:
        new_unit = Unit(
            name=unit.name,
            cluster_id=new_cluster.id,
            address=unit.address,
            latitude=unit.latitude,
            longitude=unit.longitude,
        )
        db.add(new_unit)

    db.commit()
    db.refresh(new_cluster)
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.CREATE, details=f"Created cluster {new_cluster.name} with {len(cluster.units)} units")
    db.add(audit)
    db.commit()
    return new_cluster

# Create a new unit in a cluster, only admin users can access this endpoint
@router.post("/{cluster_id}/units", response_model=UnitRead)
def create_unit(cluster_id: int, unit: UnitCreate, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    new_unit = Unit(
        name=unit.name,
        cluster_id=cluster_id,
        address=unit.address,
        latitude=unit.latitude,
        longitude=unit.longitude,
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.CREATE, details=f"Created unit {new_unit.name} in cluster {cluster_id}")
    db.add(audit)
    db.commit()
    return new_unit

# Delete a cluster, only admin users can access this endpoint
@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    cluster = db.query(Cluster).get(cluster_id)
    db.delete(cluster)
    db.commit()
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.DELETE, details=f"Deleted cluster {cluster.name}")
    db.add(audit)
    db.commit()
    return HTTPException(status_code=200, detail="Cluster deleted successfully")

# Manager get their clusters
@router.get("/my-clusters", response_model=list[ClusterRead])
def get_my_clusters(db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    if isAdmin(current_user, db):
        clusters = db.query(Cluster).all()
    else:
        clusters = db.query(Cluster).filter(Cluster.account_id == current_user.user_id).all()
    if not clusters:
        return HTTPException(status_code=404, detail="No clusters found")
    return [
        ClusterRead(
            id=cluster.id,
            name=cluster.name,
            units=[UnitRead(id=unit.id, name=unit.name) for unit in cluster.units]
        ) for cluster in clusters
    ]

# Control a unit
@router.patch(
        "/units/{unit_id}", 
        dependencies=[Depends(required_permission([PermissionEnum.CONTROL_DEVICE]))]
    )
def control_unit(
    unit_id: int, 
    node: NodeControl, 
    db: Session = Depends(get_db), 
    current_user: Account = Depends(get_current_user)
    ):
    # Get the unit of the manager
    user_id = current_user.user_id
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        return HTTPException(status_code=404, detail="Unit not found")
    if node.toggle is None and node.schedule is None:
        return HTTPException(status_code=400, detail="toggle or schedule is required")
    
    # Implement the logic to control the unit
    details = ""
    if node.toggle:
        command = COMMAND.TOGGLE
        # client.command(unit.id, command)
        details += f"Turned {unit.name} {'on' if node.toggle else 'off'}; "
    if node.schedule:
        schedule_dict = node.schedule.model_dump()
        # Raise error if turn_on_time is greater than or equal turn_off_time
        if schedule_dict['turn_on_time'] == schedule_dict['turn_off_time']:
            raise HTTPException(status_code=400, detail="turn_on_time should be less than turn_off_time")
        schedule_dict['turn_on_time'] = schedule_dict['turn_on_time'].strftime("%H:%M")
        schedule_dict['turn_off_time'] = schedule_dict['turn_off_time'].strftime("%H:%M")

        details += f"Scheduled {unit.name} to turn on at {schedule_dict['turn_on_time']} and turn off at {schedule_dict['turn_off_time']}"
        # Implement the logic to schedule the unit
        # client.command(unit.id, COMMAND.SCHEDULE, **schedule_dict)
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.UPDATE, details=details)
    db.add(audit)
    db.commit()
    return HTTPException(status_code=200, detail="Controlled the unit successfully")
