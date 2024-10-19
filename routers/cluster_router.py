from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.Account import Account, Role
from models.Audit import ActionEnum
from models.unit import Cluster, Unit
from utils import save_audit_log
from .dependencies import get_current_user, admin_required, required_permission
from schemas import ClusterCreate, ClusterRead, ClusterReadFull, ClusterUpdate, NodeControl, UnitCreate, UnitRead
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
@router.get("/", 
            response_model=list[ClusterReadFull], 
            dependencies=[Depends(required_permission([PermissionEnum.MONITOR_SYSTEM]))]
)
def get_clusters(
    db: Session = Depends(get_db)):
    # Join the Cluster and Unit tables to get all the clusters and their units
    clusters = db.query(Cluster).options(
        joinedload(Cluster.units),
    ).all()
    return clusters

# Create a new cluster, only admin users can access this endpoint
@router.post("/", response_model=ClusterRead)
def create_cluster(cluster: ClusterCreate, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    new_cluster = Cluster(
    name=cluster.name,
)
    db.add(new_cluster)
    db.commit()
    db.refresh(new_cluster)

    for unit in cluster.units:
        new_unit = Unit(
            name=unit.name,
            cluster_id=new_cluster.id,
            address=unit.address,
        )
        db.add(new_unit)

    db.commit()
    db.refresh(new_cluster)
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.CREATE, f"Tạo cluster {new_cluster.name}")
    return new_cluster

# Create a new unit in a cluster, only admin users can access this endpoint
@router.post("/{cluster_id}/units", response_model=UnitRead)
def create_unit(cluster_id: int, unit: UnitCreate, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    new_unit = Unit(
        name=unit.name,
        cluster_id=cluster_id,
        address=unit.address,
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.CREATE, f"Tạo unit {new_unit.name}")
    return new_unit

# Update cluster
@router.patch("/{cluster_id}", response_model=ClusterRead, dependencies=[Depends(required_permission([PermissionEnum.CONFIG_DEVICE]))])
def update_cluster(cluster_id: int, cluster: ClusterUpdate, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    db.query(Cluster).filter(Cluster.id == cluster_id).update({"name": cluster.name})
    db.commit()
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.UPDATE, f"Cập nhật cụm {cluster.name}")
    return db.query(Cluster).get(cluster_id)

# Delete a cluster, only admin users can access this endpoint
@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    cluster = db.query(Cluster).get(cluster_id)
    db.delete(cluster)
    db.commit()
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.DELETE, f"Xóa cluster {cluster.name}")
    return HTTPException(status_code=200, detail="Cluster deleted successfully")

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
        details += f"{'Bật' if node.toggle else 'Tắt'} {unit.name};"
        # Save to the database
        db.query(Unit).filter(Unit.id == unit_id).update({"toggle": node.toggle})
    if node.schedule:
        schedule_dict = node.schedule.model_dump()
        # Raise error if turn_on_time is greater than or equal turn_off_time
        if schedule_dict['turn_on_time'] == schedule_dict['turn_off_time']:
            raise HTTPException(status_code=400, detail="turn_on_time should be less than turn_off_time")
        schedule_dict['turn_on_time'] = schedule_dict['turn_on_time'].strftime("%H:%M")
        schedule_dict['turn_off_time'] = schedule_dict['turn_off_time'].strftime("%H:%M")

        details += f"Hẹn giờ {unit.name} mở từ {schedule_dict['turn_on_time']} đến {schedule_dict['turn_off_time']}"
        db.query(Unit).filter(Unit.id == unit_id).update({"on_time": schedule_dict['turn_on_time'], "off_time": schedule_dict['turn_off_time']})
        # Implement the logic to schedule the unit
        # client.command(unit.id, COMMAND.SCHEDULE, **schedule_dict)
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.UPDATE, details)
    return HTTPException(status_code=200, detail="Controlled the unit successfully")
