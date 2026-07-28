from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import models, database, whatsapp_utils

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="نظام السوبر ماركت")

# إعداد مجلد القوالب (واجهات الموقع)
templates = Jinja2Templates(directory="supermarket_dashboard_project/templates")

# ==========================================
# واجهات لوحة التحكم (الموقع)
# ==========================================

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(database.get_db)):
    departments = db.query(models.Department).all()
    products = db.query(models.Product).all()
    return templates.TemplateResponse("index.html", {"request": request, "departments": departments, "products": products})

@app.post("/admin/add-department")
async def add_department(name: str = Form(...), description: str = Form(""), db: Session = Depends(database.get_db)):
    new_dept = models.Department(name=name, description=description)
    db.add(new_dept)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/add-product")
async def add_product(
    name: str = Form(...), 
    price: float = Form(...), 
    description: str = Form(""), 
    department_id: int = Form(...),
    db: Session = Depends(database.get_db)
):
    new_product = models.Product(name=name, price=price, description=description, department_id=department_id)
    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/delete-product/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# ==========================================
# استقبال رسائل الواتساب (البوت)
# ==========================================
@app.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(database.get_db)):
    data = await request.json()
    try:
        event = data.get('event')
        if event == 'message' and not data['payload']['fromMe']:
            payload = data['payload']
            phone_number = payload['from'].split('@')[0]
            text = payload['body']
            
            customer = db.query(models.Customer).filter(models.Customer.phone == phone_number).first()
            if not customer:
                new_customer = models.Customer(phone=phone_number, name="زبون جديد")
                db.add(new_customer)
                db.commit()
            
            if text.isdigit():
                dept_id = int(text)
                products = db.query(models.Product).filter(models.Product.department_id == dept_id).all()
                if products:
                    msg = "🛒 المنتجات المتاحة:

"
                    for p in products:
                        msg += f"🔹 {p.name} - السعر: {p.price} دينار
"
                    whatsapp_utils.send_whatsapp_text(phone_number, msg)
                else:
                    whatsapp_utils.send_whatsapp_text(phone_number, "عذراً، القسم فارغ أو الرقم غير صحيح.")
            else:
                departments = db.query(models.Department).all()
                if not departments:
                    whatsapp_utils.send_whatsapp_text(phone_number, "أهلاً بك! السوبر ماركت قيد التجهيز.")
                else:
                    msg = "أهلاً بك في السوبر ماركت 🛒
يرجى الرد برقم القسم لعرض المنتجات:

"
                    for dept in departments:
                        msg += f"{dept.id}. {dept.name}
"
                    whatsapp_utils.send_whatsapp_text(phone_number, msg)
    except Exception as e:
        pass
    return {"status": "ok"}
