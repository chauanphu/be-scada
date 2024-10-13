from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from models.Account import Account
from models.unit import Cluster, Unit

from .dependencies import get_current_user, admin_required
from schemas import ClusterCreate, ClusterRead, ClusterReadFull, UnitCreate, UnitRead
from database.session import get_db

router = APIRouter(
    prefix='/clusters',
    tags=['clusters']
)

# Get all clusters, only admin users can access this endpoint
@router.get("/", response_model=list[ClusterReadFull])
def get_clusters(db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
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
    return new_cluster

# Delete a cluster, only admin users can access this endpoint
@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    cluster = db.query(Cluster).get(cluster_id)
    db.delete(cluster)
    db.commit()
    return {"message": "Cluster deleted successfully"}

# Manager get their clusters
@router.get("/my-clusters", response_model=list[ClusterReadFull])
def get_my_clusters(db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    clusters = db.query(Cluster).filter(Cluster.account_id == current_user.user_id).all()
    return clusters

