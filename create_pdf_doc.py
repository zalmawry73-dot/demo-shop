import sys
from weasyprint import HTML

def create_pdf():
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>Planning and Analysis Phase</title>
        <style>
            @page {
                size: A4;
                margin: 2.5cm;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: 'Arial', sans-serif;
                    font-size: 10pt;
                }
            }
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #fff;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 0;
            }
            h2 {
                color: #2980b9;
                margin-top: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            h3 {
                color: #16a085;
                margin-top: 20px;
            }
            h4 {
                color: #555;
                margin-bottom: 5px;
            }
            ul, ol {
                margin-bottom: 15px;
            }
            li {
                margin-bottom: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: right;
            }
            th {
                background-color: #f7f9f9;
                color: #2c3e50;
            }
            .signature {
                margin-top: 60px;
                text-align: left;
                font-weight: bold;
                border-top: 1px solid #ccc;
                display: inline-block;
                padding-top: 10px;
                padding-right: 20px;
                padding-left: 20px;
            }
            .meta {
                color: #777;
                font-size: 0.9em;
                margin-bottom: 30px;
            }
        </style>
    </head>
    <body>

        <h1>وثيقة التخطيط والتحليل (Planning & Analysis Phase)</h1>
        
        <div class="meta">
            <strong>اسم المشروع:</strong> نظام المتجر المؤسسي المتكامل (Enterprise Store Platform)<br>
            <strong>الإصدار:</strong> 1.0<br>
            <strong>التاريخ:</strong> 13 يناير 2026
        </div>

        <h2>1. مقدمة (Introduction)</h2>
        <p>تعد مرحلة التخطيط والتحليل حجر الزاوية في دورة حياة تطوير النظام (SDLC). في هذه الوثيقة، نستعرض الرؤية الشاملة لنظام التجارة الإلكترونية الذي نقوم بتطويره، والذي يهدف إلى توفير حل تقني متقدم، قابل للتوسع، ويلبي احتياجات السوق المتغيرة. لا يقتصر هدفنا على بناء "متجر إلكتروني" تقليدي، بل نسعى لتأسيس بنية تحتية رقمية قوية تدعم العمليات التجارية المعقدة وتوفر تجربة مستخدم استثنائية.</p>

        <h2>2. تحديد النطاق (Project Scope)</h2>
        <h3>الهدف العام</h3>
        <p>بناء نظام <strong>Single-Tenant Enterprise E-commerce Platform</strong> (منصة تجارة إلكترونية مؤسسية) مصممة لخدمة الكيانات التجارية ذات الحجم المتوسط إلى الكبير. يركز النظام على الأداء العالي، المرونة في تخصيص قواعد العمل (Business Rules)، والتكامل السلس بين المكونات المختلفة (المخزون، المبيعات، العملاء).</p>

        <h3>حدود النظام (Boundaries)</h3>
        <ul>
            <li><strong>نوع النظام:</strong> نظام داخلي (In-house Hosted) أو سحابي خاص (Private Cloud). ليس نظام SaaS متعدد المتاجر (Multi-Tenant) في مرحلته الحالية، مما يسمح بتركيز الموارد على تخصيص التجربة لمتجر واحد ضخم.</li>
            <li><strong>المستخدمون المستهدفون:</strong>
                <ul>
                    <li><strong>المديرون (Admins):</strong> للتحكم الكامل في المنتجات، الطلبات، والإعدادات.</li>
                    <li><strong>العملاء (Customers):</strong> تجربة تسوق سلسة من التصفح حتى الدفع.</li>
                    <li><strong>مديرو المخزون:</strong> لتتبع الكميات وحركات التوريد.</li>
                </ul>
            </li>
        </ul>

        <h2>3. جمع المتطلبات (Requirements Gathering)</h2>
        <h3>3.1 المتطلبات الوظيفية (Functional Requirements)</h3>
        <p>تم تقسيم النظام إلى وحدات معيارية (Modules) لضمان الفصل المنطقي بين الخدمات:</p>

        <h4>أ. وحدة إدارة الكتالوج (Catalog Management)</h4>
        <ul>
            <li><strong>المنتجات:</strong> دعم أنواع متعددة (منتجات مادية، رقمية، خدمات، أطعمة).</li>
            <li><strong>الخيارات والسمات (Variants & Attributes):</strong> نظام ديناميكي لإنشاء متغيرات معقدة (مثل: اللون، الحجم، القماش) مع تأثيرات متباينة على السعر والوزن.</li>
            <li><strong>التصنيفات (Categories):</strong> هيكل شجري (Tree Structure) غير محدود المستويات لتنظيم المنتجات.</li>
            <li><strong>الحقول المخصصة (Custom Fields):</strong> إمكانية إضافة حقول بيانات إضافية للمنتجات دون تعديل الكود البرمجي.</li>
        </ul>

        <h4>ب. وحدة المبيعات والطلبات (Sales & Orders)</h4>
        <ul>
            <li><strong>سلة الشراء:</strong> سلة ذكية تتحقق من صحة المخزون والأسعار لحظياً.</li>
            <li><strong>إدارة الطلبات:</strong> دورة حياة كاملة (Pending -> Processing -> Shipped -> Delivered -> Cancelled).</li>
            <li><strong>القيود والشروط (Advanced Constraints):</strong> محرك قواعد متطور للتحكم في طرق الدفع والشحن المتاحة بناءً على:
                <ul>
                    <li>محتوى السلة (منتجات معينة، تصنيفات).</li>
                    <li>إجمالي القيمة أو الوزن.</li>
                    <li>موقع العميل الجغرافي.</li>
                    <li>توقيت الطلب.</li>
                </ul>
            </li>
        </ul>

        <h4>ج. وحدة المخزون (Inventory Management)</h4>
        <ul>
            <li><strong>تتبع دقيق:</strong> خصم الكميات عند إتمام الطلب (أو عند الحجز).</li>
            <li><strong>تنبيهات المخزون:</strong> إشعارات آلية عند انخفاض الكمية عن حد الطلب.</li>
            <li><strong>تاريخ الحركات:</strong> سجل كامل (Audit Log) لكل حركة دخول أو خروج للمخزون.</li>
        </ul>

        <h4>د. إدارة العملاء (Customer Management)</h4>
        <ul>
            <li><strong>الملفات الشخصية:</strong> سجل شامل لبيانات العميل، عناوينه، وتاريخ طلباته.</li>
            <li><strong>مجموعات العملاء:</strong> تصنيف العملاء (VIP, جملة، أفراد) لتطبيق خصومات أو قواعد خاصة.</li>
        </ul>

        <h4>هـ. التسويق (Marketing)</h4>
        <ul>
            <li><strong>الكوبونات:</strong> محرك قسائم مرن يدعم الخصم الثابت أو النسبي، مع شروط استخدام متعددة.</li>
            <li><strong>العروض الترويجية:</strong> خصومات تلقائية بناءً على قواعد محددة.</li>
        </ul>

        <h4>و. الإعدادات والتهيئة (System Configuration)</h4>
        <ul>
            <li><strong>إعدادات المتجر:</strong> الاسم، الشعار، العملات، الضرائب.</li>
            <li><strong>الأمان:</strong> إعدادات الجلسات، سياسات كلمات المرور، والتحقق الثنائي (2FA).</li>
        </ul>

        <h3>3.2 المتطلبات غير الوظيفية (Non-Functional Requirements)</h3>
        <ul>
            <li><strong>الأداء (Performance):</strong> استجابة واجهات برمجة التطبيقات (API Response Time) يجب أن تكون أقل من 200ms للعمليات الأساسية. دعم آلاف الاتصالات المتزامنة.</li>
            <li><strong>القابلية للتوسع (Scalability):</strong> تصميم النظام يتبع معمارية <strong>Modular Monolith</strong> التي تسمح بفصل أي وحدة وتحويلها إلى خدمة مصغرة.</li>
            <li><strong>الأمان وحماية البيانات (Security):</strong> تشفير كامل لكلمات المرور (Bcrypt). استخدام بروتوكول OAuth2 مع JWT. حماية ضد SQL Injection, XSS.</li>
            <li><strong>الصيانة:</strong> الالتزام بمبادئ Clean Code و SOLID. توثيق Swagger. تغطية اختبارية.</li>
        </ul>

        <h2>4. دراسة الجدوى التقنية (Technical Feasibility & Stack)</h2>
        <ul>
            <li><strong>لغة البرمجة: Python 3.10+</strong> (بيئة غنية، دعم AI، سهولة الصيانة).</li>
            <li><strong>إطار العمل الخلفي: FastAPI</strong> (سريع، Async، توثيق تلقائي).</li>
            <li><strong>قاعدة البيانات: PostgreSQL</strong> (موثوقية، علاقات معقدة).</li>
            <li><strong>الواجهة الأمامية: Hybrid (Jinja2 + JS)</strong> (سرعة، SEO، تفاعلية).</li>
        </ul>

        <h2>5. تحليل المخاطر (Risk Analysis)</h2>
        <table>
            <thead>
                <tr>
                    <th>الخطر</th>
                    <th>الاحتمالية</th>
                    <th>التأثير</th>
                    <th>استراتيجية التخفيف</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>تعقيد قواعد العمل</td>
                    <td>مرتفع</td>
                    <td>مرتفع</td>
                    <td>استخدام محرك قواعد مرن واختبارات مكثفة.</td>
                </tr>
                <tr>
                    <td>مشاكل الأداء مع البيانات الضخمة</td>
                    <td>متوسط</td>
                    <td>مرتفع</td>
                    <td>تطبيق التصحيف (Pagination) والفهارس (Indexes).</td>
                </tr>
                <tr>
                    <td>تغيير المتطلبات</td>
                    <td>مرتفع</td>
                    <td>متوسط</td>
                    <td>اعتماد منهجية Agile وتصميم معياري.</td>
                </tr>
            </tbody>
        </table>

        <h2>6. الخاتمة (Conclusion)</h2>
        <p>يمثل هذا النظام نقلة نوعية في طريقة إدارة العمليات التجارية. من خلال التركيز على المتانة التقنية في مرحلة التخطيط والتحليل، نضمن بناء أساس قوي قادر على استيعاب النمو المستقبلي وتحقيق أهداف العمل بكفاءة عالية.</p>

        <div class="signature">
            إعداد وكتابة:<br>
            <span style="font-size: 1.2em; color: #2c3e50;">م/ زكريا الماوري</span><br>
            <span style="font-weight: normal; font-size: 0.9em; color: #777;">Lead Software Engineer / System Architect</span>
        </div>

    </body>
    </html>
    """
    
    try:
        HTML(string=html_content).write_pdf(target="d:/Store/docs/Planning_and_Analysis_Phase.pdf")
        print("PDF created successfully: d:/Store/docs/Planning_and_Analysis_Phase.pdf")
    except Exception as e:
        print(f"Error creating PDF: {e}")

if __name__ == "__main__":
    create_pdf()
