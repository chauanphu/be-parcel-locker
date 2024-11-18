from states.shipment import Route, Location, Order as VRPOrder, set_route
from database.session import get_db
from models.order import Order, OrderStatus
from models.locker import Locker
from sqlalchemy.orm import Session

def db_order_to_vrp_order(db_order: Order) -> VRPOrder:
    return VRPOrder(
        db_order.order_id,
        db_order.parcel.weight if db_order.parcel else 0,
        db_order.parcel.parcel_size if db_order.parcel else "S"
    )

def get_active_orders_and_locations(db: Session):
    # Get all ongoing orders
    active_orders = db.query(Order).filter(Order.order_status == OrderStatus.Ongoing).all()
    
    # Get all unique locker locations
    lockers: dict[str, Location] = {}
    for order in active_orders:
        # Sending lockers
        if order.sending_cell.locker_id not in lockers:
            locker = db.query(Locker).filter(Locker.locker_id == order.sending_cell.locker_id).first()
            lockers[locker.locker_id] = Location(locker.locker_id, locker.latitude, locker.longitude)
            lockers[locker.locker_id].pickup_orders = []
            
        # Receiving lockers
        if order.receiving_cell.locker_id not in lockers:
            locker = db.query(Locker).filter(Locker.locker_id == order.receiving_cell.locker_id).first()
            lockers[locker.locker_id] = Location(locker.locker_id, locker.latitude, locker.longitude)
            lockers[locker.locker_id].dropoff_orders = []
        
        # Convert and assign orders
        vrp_order: VRPOrder = db_order_to_vrp_order(order)
        lockers[order.sending_cell.locker_id].pickup_orders.append(vrp_order)
        lockers[order.receiving_cell.locker_id].dropoff_orders.append(vrp_order)
    
    return list(lockers.values())

# Create and set up route with real data
db = next(get_db())
locations = get_active_orders_and_locations(db)
route = Route(1)
route.visit_locations = locations

# Store route in Redis
set_route(route)
