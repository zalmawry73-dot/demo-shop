import sys
from weasyprint import HTML

def create_pdf():
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>مرحلة تصميم النظام (System Design)</title>
        <style>
            @page {
                size: A4;
                margin: 2cm;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: 'Arial', sans-serif;
                    font-size: 10pt;
                }
            }
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.5;
                color: #333;
                background-color: #fff;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
                margin-top: 0;
                text-align: center;
                font-size: 24pt;
            }
            h2 {
                color: #2980b9;
                margin-top: 30px;
                border-right: 5px solid #2980b9;
                padding-right: 15px;
                background-color: #f4f6f7;
                padding: 10px;
                font-size: 18pt;
            }
            h3 {
                color: #16a085;
                margin-top: 20px;
                border-bottom: 1px dashed #ccc;
                padding-bottom: 5px;
                font-size: 14pt;
            }
            p { margin-bottom: 15px; text-align: justify; }
            ul { margin-bottom: 15px; list-style-type: square; }
            
            /* Diagram Styles via CSS */
            .diagram-box {
                border: 2px solid #555;
                padding: 15px;
                margin: 20px 0;
                background-color: #f9f9f9;
                border-radius: 8px;
                text-align: center;
            }
            .module-box {
                display: inline-block;
                border: 2px solid #34495e;
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin: 10px;
                font-weight: bold;
                border-radius: 5px;
                width: 120px;
            }
            .arrow {
                font-size: 20px;
                color: #e74c3c;
                font-weight: bold;
            }
            
            /* Table Styles for Schema/API */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 10pt;
            }
            th, td {
                border: 1px solid #bdc3c7;
                padding: 8px;
                text-align: right;
            }
            th {
                background-color: #34495e;
                color: #fff;
            }
            tr:nth-child(even) { background-color: #f2f2f2; }
            
            /* Code/Algorithm Blocks */
            .code-block {
                font-family: 'Courier New', monospace;
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                direction: ltr;
                text-align: left;
                font-size: 9pt;
                white-space: pre-wrap;
            }
            
            .signature {
                margin-top: 80px;
                border-top: 2px solid #333;
                padding-top: 20px;
                width: 300px;
            }
        </style>
    </head>
    <body>

        <h1>وثيقة تصميم النظام<br><span style="font-size: 0.6em; color: #7f8c8d;">System Design Specification</span></h1>
        
        <div style="text-align: center; margin-bottom: 40px; color: #555;">
            <strong>اسم المشروع:</strong> نظام المتجر المؤسسي المتكامل<br>
            <strong>الإصدار:</strong> 1.0 <br>
            <strong>التاريخ:</strong> 13 يناير 2026
        </div>

        <h2>1. هندسة النظام (System Architecture)</h2>
        <p>لقد قمت باعتمار معمارية <strong>Modular Monolith</strong> لتصميم هذا النظام. هذا الخيار هو الأنسب حالياً لأنه يجمع بين بساطة النشر (Deployment) وقوة الفصل المنطقي (Logical Separation) التي تمهد الطريق للخدمات المصغرة (Microservices) في المستقبل.</p>
        
        <div class="diagram-box">
            <h3>المخطط المعماري للنظام</h3>
            <div>
                <div class="module-box">Frontend<br>(Jinja2/JS)</div>
                <span class="arrow">⬇ ⬆</span>
                <div class="module-box">API Gateway<br>(FastAPI)</div>
            </div>
            <div style="margin-top: 20px;">
                <span class="arrow">⬇</span>
            </div>
            <div style="border: 2px dashed #95a5a6; padding: 20px; margin: 20px; display: inline-block; border-radius: 10px;">
                <strong>Core Modules (Business Logic)</strong><br><br>
                <div class="module-box" style="background: #d4e6f1;">Catalog</div>
                <div class="module-box" style="background: #d4e6f1;">Sales</div>
                <div class="module-box" style="background: #d4e6f1;">Inventory</div>
                <div class="module-box" style="background: #d4e6f1;">Customers</div>
                <div class="module-box" style="background: #d4e6f1;">Auth</div>
            </div>
            <div style="margin-top: 20px;">
                <span class="arrow">⬇</span>
            </div>
            <div>
                <div class="module-box" style="background: #fadbd8;">PostgreSQL<br>(Database)</div>
                <div class="module-box" style="background: #fadbd8;">Redis<br>(Cache)</div>
            </div>
        </div>

        <h2>2. تصميم قاعدة البيانات (Database Schema - ERD)</h2>
        <p>لقد قمت بتصميم المخطط العلائقي (ERD) لضمان تكامل البيانات وسرعة الاستعلام. فيما يلي أهم الجداول والعلاقات:</p>

        <h3>أ. الكتالوج والمنتجات (Catalog Module)</h3>
        <p>المنتج هو قلب النظام. العلاقة بين المنتج والخيارات (Variants) هي 1:N.</p>
        <table>
            <thead>
                <tr>
                    <th>الجدول (Table)</th>
                    <th>الوصف</th>
                    <th>أهم الأعمدة (Columns)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>products</strong></td>
                    <td>الجدول الرئيسي للمنتجات</td>
                    <td>id, name, slug, product_type, category_id, brand_id</td>
                </tr>
                <tr>
                    <td><strong>product_variants</strong></td>
                    <td>المتغيرات (مثل: قميص أحمر مقاس L)</td>
                    <td>id, product_id, sku, price, stock_qty, attributes (JSON)</td>
                </tr>
                <tr>
                    <td><strong>categories</strong></td>
                    <td>التصنيفات (شجري)</td>
                    <td>id, name, parent_id, lft, rgt (for tree traversal)</td>
                </tr>
            </tbody>
        </table>

        <h3>ب. المبيعات والطلبات (Sales Module)</h3>
        <p>يرتبط  الطلب بالعميل (1:N) وبالمنتجات عبر جدول وسيط (OrderItems).</p>
        <table>
            <thead>
                <tr>
                    <th>الجدول (Table)</th>
                    <th>الوصف</th>
                    <th>أهم الأعمدة (Columns)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>orders</strong></td>
                    <td>رأس الطلب</td>
                    <td>id, user_id, status, total_amount, shipping_address_id</td>
                </tr>
                <tr>
                    <td><strong>order_items</strong></td>
                    <td>تفاصيل المنتجات في الطلب</td>
                    <td>id, order_id, variant_id, quantity, unit_price, total</td>
                </tr>
                <tr>
                    <td><strong>cart_items</strong></td>
                    <td>سلة الشراء المؤقتة</td>
                    <td>id, session_id, variant_id, quantity</td>
                </tr>
            </tbody>
        </table>

         <h3>ج. المخزون (Inventory Module)</h3>
        <table>
            <thead>
                <tr>
                    <th>الجدول (Table)</th>
                    <th>الوصف</th>
                    <th>أهم الأعمدة (Columns)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>inventory_transactions</strong></td>
                    <td>سجل حركات المخزون</td>
                    <td>id, variant_id, quantity_change, type (IN/OUT), reference_id</td>
                </tr>
            </tbody>
        </table>

        <h2>3. خوارزميات النظام (Core Algorithms)</h2>
        <p>لضمان دقة العمليات، قمت بتصميم الخوارزميات التالية للتعامل مع العمليات الحساسة:</p>

        <h3>أ. خوارزمية خصم المخزون (Inventory Deduction) - Pseudo Code</h3>
        <div class="code-block">
FUNCTION ProcessOrder(Order order):
    START TRANSACTION
    
    FOR EACH item IN order.items:
        # 1. Lock Row for Update (تأمين الصف لمنع التضارب)
        current_stock = SELECT stock FROM variants 
                        WHERE id = item.variant_id 
                        FOR UPDATE
        
        # 2. Check Availability
        IF current_stock < item.quantity:
            ROLLBACK
            RETURN Error("Out of Stock: " + item.product_name)
            
        # 3. Deduct
        UPDATE variants 
        SET stock = stock - item.quantity 
        WHERE id = item.variant_id
        
        # 4. Log Transaction
        INSERT INTO inventory_transactions (
            variant_id, qty, type, ref_order
        ) VALUES (
            item.variant_id, -item.quantity, 'SALE', order.id
        )
    END FOR
    
    COMMIT TRANSACTION
    RETURN Success
        </div>

        <h3>ب. خوارزمية مطابقة القيود (Constraint Matching Engine)</h3>
        <p>تستخدم هذه الخوارزمية لتحديد ما إذا كانت طريقة الدفع/الشحن متاحة للعميل الحالي.</p>
        <div class="code-block">
FUNCTION EvaluateConstraints(Constraints list, Context ctx):
    ValidOptions = []
    
    FOR EACH constraint IN list:
        IsMatch = True
        
        FOR EACH condition IN constraint.conditions:
            # Check Condition Type
            IF condition.type == 'CART_TOTAL':
                IF ctx.cart_total < condition.min OR ctx.cart_total > condition.max:
                    IsMatch = False
                    BREAK
            
            IF condition.type == 'LOCATION':
                IF ctx.user_city NOT IN condition.allowed_cities:
                    IsMatch = False
                    BREAK
                    
            # ... check other conditions
            
        END FOR
        
        IF IsMatch == True:
            ValidOptions.add(constraint.target_option)
            
    RETURN ValidOptions
        </div>

        <h2>4. تصميم واجهة برمجة التطبيقات (API Design)</h2>
        <p>لقد قمت بتصميم نقاط النهاية (Endpoints) وفق معايير RESTful لضمان سهولة الاستخدام والتكامل:</p>
        
        <table>
            <thead>
                <tr>
                    <th>الطريقة (Method)</th>
                    <th>المسار (Endpoint)</th>
                    <th>الوصف</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>GET</td>
                    <td>/api/products</td>
                    <td>جلب قائمة المنتجات (مع دعم التصفية والبحث)</td>
                </tr>
                <tr>
                    <td>GET</td>
                    <td>/api/products/{id}</td>
                    <td>تفاصيل منتج معين شاملة المتغيرات</td>
                </tr>
                <tr>
                    <td>POST</td>
                    <td>/api/cart/items</td>
                    <td>إضافة منتج للسلة</td>
                </tr>
                <tr>
                    <td>POST</td>
                    <td>/api/orders</td>
                    <td>إنشاء طلب جديد (Checkout)</td>
                </tr>
                <tr>
                    <td>GET</td>
                    <td>/api/orders/{id}</td>
                    <td>تتبع حالة الطلب</td>
                </tr>
                 <tr>
                    <td>GET</td>
                    <td>/api/settings/constraints/payment</td>
                    <td>جلب قيود الدفع المتاحة</td>
                </tr>
            </tbody>
        </table>

        <h2>5. رحلة المستخدم وتصميم الواجهة (UI/UX Journey)</h2>
        <div class="diagram-box">
            <strong>رحلة العميل (Customer Journey Map)</strong><br><br>
            <span class="module-box" style="width:auto">زيارة المتجر</span>
            <span class="arrow">➡</span>
            <span class="module-box" style="width:auto">تصفح المنتجات<br>(Filter/Search)</span>
            <span class="arrow">➡</span>
            <span class="module-box" style="width:auto">صفحة المنتج<br>(تحديد الخيارات)</span>
            <br><br>
            <span class="arrow">⬇</span>
            <br><br>
            <span class="module-box" style="width:auto">إضافة للسلة</span>
            <span class="arrow">➡</span>
            <span class="module-box" style="width:auto">إتمام الطلب (Checkout)<br>(Login -> Address -> Payment)</span>
            <span class="arrow">➡</span>
            <span class="module-box" style="width:auto">الدفع والتأكيد</span>
        </div>

        <div class="signature">
            <strong>إعداد وتصميم:</strong><br><br>
            <span style="font-size: 1.4em; color: #2c3e50;">م/ زكريا الماوري</span><br>
            <span style="color: #555;">Lead System Architect</span>
        </div>

    </body>
    </html>
    """
    
    try:
        HTML(string=html_content).write_pdf(target="d:/Store/docs/System_Design_Phase.pdf")
        print("Success: d:/Store/docs/System_Design_Phase.pdf")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_pdf()
