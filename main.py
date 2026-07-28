from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import subprocess  # ضفنا هذه المكتبة حتى نكدر نسحب التحديثات من GitHub
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

# إضافة مسار التقارير الجديد اللي ضفنا الزر مالته
@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports(request: Request, db: Session = Depends(database.get_db)):
    # حساب عدد الزبائن والمنتجات لعرضها بالتقارير
    customer_count = db.query(models.Customer).count()
    product_count = db.query(models.Product).count()
    # راح نحتاج ملف reports.html بعدين
    return templates.TemplateResponse("reports.html", {"request": request, "customer_count": customer_count, "product_count": product_count})

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

# مسار تحديث السيرفر من GitHub (زر المزامنة)
@app.post("/admin/pull-update")
async def pull_update():
    try:
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
                    # تم إصلاح طريقة كتابة النصوص متعددة الأسطر باستخدام \n
                    msg = "🛒 المنتجات المتاحة:\n\n"
                    for p in products:
                        msg += f"🔹 {p.name} - السعر: {p.price} دينار\n"
                    whatsapp_utils.send_whatsapp_text(phone_number, msg)
                else:
                    whatsapp_utils.send_whatsapp_text(phone_number, "عذراً، القسم فارغ أو الرقم غير صحيح.")
            else:
                departments = db.query(models.Department).all()
                if not departments:
                    whatsapp_utils.send_whatsapp_text(phone_number, "أهلاً بك! السوبر ماركت قيد التجهيز.")
                else:
                    msg = "أهلاً بك في السوبر ماركت 🛒\nيرجى الرد برقم القسم لعرض المنتجات:\n\n"
                    for dept in departments:
                        msg += f"{dept.id}. {dept.name}\n"
                    whatsapp_utils.send_whatsapp_text(phone_number, msg)
    except Exception as e:
        # طباعة الخطأ بدل تجاهله حتى نعرف الخلل إذا صار
        print(f"Error processing webhook: {e}") 
    return {"status": "ok"}
