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
    if cluster.units is None:
        return new_cluster
    if len(cluster.units) == 0:
        return new_cluster
    for unit in cluster.units:  
        new_unit = Unit(
            name=unit.name,
            cluster_id=new_cluster.id,
            mac=unit.mac,
        )
        print
        db.add(new_unit)

    db.commit()
    db.refresh(new_cluster)
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.CREATE, f"Tạo cluster {new_cluster.name}")
    return new_cluster

@router.put("/{cluster_id}", response_model=ClusterRead, dependencies=[Depends(required_permission([PermissionEnum.CONFIG_DEVICE]))])
def update_cluster(cluster_id: int, cluster: ClusterUpdate, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    db.query(Cluster).filter(Cluster.id == cluster_id).update({"name": cluster.name})
    db.commit()
    # Update the units, create new units if no id is provided
    if cluster.units is not None:
        for unit in cluster.units:
            if unit.id is None:
                new_unit = Unit(
                    name=unit.name,
                    cluster_id=cluster_id,
                    mac=unit.mac,
                )
                db.add(new_unit)
            else:
                db.query(Unit).filter(Unit.id == unit.id).update({"name": unit.name, "mac": unit.mac})
    db.commit()
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.UPDATE, f"Cập nhật cụm {cluster.name}")
    return db.query(Cluster).get(cluster_id)

# Create a new unit in a cluster, only admin users can access this endpoint
@router.post("/{cluster_id}/units", response_model=UnitRead)
def create_unit(cluster_id: int, unit: UnitCreate, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    new_unit = Unit(
        name=unit.name,
        cluster_id=cluster_id,
        mac=unit.mac,
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

def handle_toggle(db, unit_id, toggle):
    db.query(Unit).filter(Unit.id == unit_id).update({"toggle": toggle})
    db.commit()
    # Implement the logic to control the unit
    # client.command(unit_id, COMMAND.TOGGLE, toggle)
    return HTTPException(status_code=200, detail="Controlled the unit successfully")

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
    
    # Implement the logic to control the unit
    details = ""
    if node.type == "toggle":
        # client.command(unit.id, command)
        details += f"{'Bật' if node.payload else 'Tắt'} {unit.name};"
        # Save to the database
        db.query(Unit).filter(Unit.id == unit_id).update({"toggle": node.payload})
        payload = "on" if node.payload else "off"
        client.command(unit.id, COMMAND.TOGGLE, payload)

    if node.type == "schedule":
        schedule_dict = node.payload.model_dump()
        turn_on_time = f"{schedule_dict['hourOn']}:{schedule_dict['minuteOn']}"
        turn_off_time = f"{schedule_dict['hourOff']}:{schedule_dict['minuteOff']}"
        if turn_on_time > turn_off_time:
            return HTTPException(status_code=400, detail="Thời gian bật phải nhỏ hơn thời gian tắt")
        details += f"Hẹn giờ {unit.name} mở từ {turn_on_time} đến {turn_off_time}"
        db.query(Unit).filter(Unit.id == unit_id).update({"on_time": turn_on_time, "off_time": turn_off_time})
        # Implement the logic to schedule the unit
        payload = {
            "hour_on": node.payload.hourOn,
            "minute_on": node.payload.minuteOn,
            "hour_off": node.payload.hourOff,
            "minute_off": node.payload.minuteOff
        }
        client.command(unit.id, COMMAND.SCHEDULE, payload)
    # Audit the action
    save_audit_log(db, current_user.email, ActionEnum.UPDATE, details)
    return HTTPException(status_code=200, detail="Controlled the unit successfully")
