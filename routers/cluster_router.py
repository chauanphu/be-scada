from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from models.Account import Account
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
    dependencies=[Depends(required_permission(PermissionEnum.MONITOR_SYSTEM))]
)

# Get all clusters, only admin users can access this endpoint
@router.get("/", response_model=list[ClusterReadFull])
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
    clusters = db.query(Cluster).filter(Cluster.account_id == current_user.user_id).all()
    return clusters

# PATCH /my-clusters/{cluster_id}
@router.patch("/my-clusters/{cluster_id}")
def control_cluster(cluster_id: int, node: NodeControl, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    # Get all units in the cluster of the manager
    user_id = current_user.user_id
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()

    if current_user.role == 1:
        units = db.query(Unit).join(Cluster).filter(Cluster.id == cluster_id).all()
    else:
        units = db.query(Unit).join(Cluster).filter(Cluster.account_id == user_id).all()
    # Implement the logic to control the units
    details = f"Set all units in cluster {cluster.name}: "
    if node.toggle is None and node.schedule is None:
        return HTTPException(status_code=400, detail="toggle or schedule is required")
    for unit in units:
        # Publish the control message to the unit
        if node.toggle:
            command = COMMAND.ON if node.toggle else COMMAND.OFF
            client.command(unit.id, command)
        if node.schedule:
            schedule_dict = node.schedule.model_dump()
            # Raise error if turn_on_time is greater than or equal turn_off_time
            if schedule_dict['turn_on_time'] >= schedule_dict['turn_off_time']:
                return {"error": "turn_on_time should be less than turn_off_time"}
            schedule_dict['turn_on_time'] = schedule_dict['turn_on_time'].strftime("%H:%M")
            schedule_dict['turn_off_time'] = schedule_dict['turn_off_time'].strftime("%H:%M")
            # Implement the logic to schedule the unit
            client.command(unit.id, COMMAND.SCHEDULE, **schedule_dict)
    if node.toggle:
        details += f"Turned {'on' if node.toggle else 'off'}; "
    if node.schedule:
        details += f"Scheduled to turn on at {schedule_dict['turn_on_time']} and turn off at {schedule_dict['turn_off_time']}; "
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.UPDATE, details=details)
    db.add(audit)
    db.commit()
    return {"message": "Controlled the cluster successfully"}

# Control a unit
@router.patch("/my-clusters/{cluster_id}/units/{unit_id}")
def control_unit(cluster_id: int, unit_id: int, node: NodeControl, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    # Get the unit of the manager
    user_id = current_user.user_id
    if current_user.role == 1:
        unit = db.query(Unit).join(Cluster).filter(Unit.id == unit_id, Cluster.id == cluster_id).first()
    # Return error if the unit does not belong to the manager
    elif current_user.role == 2:
        unit = db.query(Unit).join(Cluster).filter(Unit.id == unit_id, Cluster.account_id == user_id).first()
        if not unit:
            return HTTPException(status_code=403, detail="Unit does not belong to the manager")
    # Return error 403 if the unit does not belong to the manager
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    details = f"Node {unit.name}: "
    if node.toggle is None and node.schedule is None:
        return HTTPException(status_code=400, detail="toggle or schedule is required")
    # Implement the logic to control the unit
    if node.toggle:
        command = COMMAND.ON if node.toggle else COMMAND.OFF
        client.command(unit.id, command)
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
        client.command(unit.id, COMMAND.SCHEDULE, **schedule_dict)
    # Audit the action
    audit = Audit(email=current_user.email, action=ActionEnum.UPDATE, details=details)
    db.add(audit)
    db.commit()
    return HTTPException(status_code=200, detail="Controlled the unit successfully")
