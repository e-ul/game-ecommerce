from fastapi import APIRouter
from fastapi import HTTPException
from models import *
from database import PrimaryEngineConn, ReadonlyEngineConn
from datetime import datetime
import random
from config import host, create_dict_from_rows
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy import func
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter(
    prefix="/order",
)

primary = PrimaryEngineConn()
readonly = ReadonlyEngineConn()


@router.get("/")
async def get_all(session: Session = Depends(readonly.get_session)):
    result = session.query(Order).all()
    return result


@router.get("/get/{id}")
async def get_order(id: int, session: Session = Depends(readonly.get_session)):
    order = session.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Data not found")

    order_dict = order.__dict__
    order_dict.pop("_sa_instance_state")  # SQLAlchemy 내부 상태 정보 제거
    order_dict.update(host())

    session.close()
    return order_dict


@router.get("/recent/{hours}")
async def get_recent_orders(hours: int, session: Session = Depends(readonly.get_session)):
    query = """
        select /* sqlid : order-recent */ o.*, c.name as customer_name, p.name as product_name
        from orders o
        join customer c on o.cust_id = c.id
        join product p on o.prd_id = p.id
        where o.last_update_time >= date_sub(now(), interval :hours hour)
        order by o.last_update_time desc
        limit 20
    """

    result = session.execute(text(query), {"hours": hours})
    rows = result.fetchall()
    columns = result.keys()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"recent {hours} hours orders not found")

    return_val = create_dict_from_rows(rows, columns)

    return return_val


@router.post("/pay")
async def order(customer_id: int, product_id: int, session: Session = Depends(primary.get_session)):
    customer = session.query(Customer).filter(
        Customer.id == customer_id).first()
    product = session.query(Product).filter(Product.id == product_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Data not found")
    if not product:
        raise HTTPException(status_code=404, detail="Data not found")

    # 주문 생성
    order_cnt = random.randint(1, 5)
    order_dt = datetime.now().strftime("%Y-%m-%d")
    order = Order(
        promo_id=None,
        order_cnt=order_cnt,
        order_price=order_cnt*product.price,
        order_dt=order_dt,
        last_update_time=datetime.now(),
        cust_id=customer_id,
        prd_id=product_id
    )

    session.add(order)
    session.commit()
    session.close()

    msg = {"message": "Order placed successfully"}
    msg.update(host())

    return msg

@router.get("/popular")
async def get_popular_products(session: Session = Depends(readonly.get_session)):
    query = """
        select /* sqlid : order-popular */ p.id, p.name, count(o.order_cnt) order_cnt
        from product p,
            orders o
        where p.id = o.prd_id
        and o.last_update_time >= date_sub(now(), interval 10 minute)
        group by p.id, p.name
        order by order_cnt desc
        limit 10
    """

    result = session.execute(text(query))
    rows = result.fetchall()
    columns = result.keys()

    return_val = create_dict_from_rows(rows, columns)

    if not return_val:
        raise HTTPException(
            status_code=404, detail="Data not found")

    return return_val

@router.get("/vip")
async def get_top_vip_customers(session: Session = Depends(readonly.get_session)):
    query = """
        select /* sqlid : order-vip */ c.id, c.username, count(o.order_cnt) order_cnt
        from customer c,
            orders o
        where c.id = o.prd_id
        and o.last_update_time >= date_sub(now(), interval 10 minute)
        group by c.id, c.username
        order by order_cnt desc
        limit 10;
    """

    result = session.execute(text(query))
    rows = result.fetchall()
    columns = result.keys()

    return_val = create_dict_from_rows(rows, columns)

    if not return_val:
        raise HTTPException(status_code=404, detail="Data not found")

    return return_val
