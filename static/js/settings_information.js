document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/general');
        if (!response.ok) throw new Error('Failed to load settings');

        const data = await response.json();

        // Tab 1: Store Info
        document.getElementById('storeName').value = data.store_name || '';
        document.getElementById('supportEmail').value = data.support_email || '';
        document.getElementById('supportPhone').value = data.support_phone || '';
        if (data.logo_url) {
            document.getElementById('logoPreview').src = data.logo_url;
        }

        // Tab 2: Commercial Activity
        document.getElementById('commercialActivityType').value = data.commercial_activity_type || 'individual';
        document.getElementById('commercialName').value = data.commercial_name || '';
        document.getElementById('commercialRegistrationName').value = data.commercial_registration_name || '';
        document.getElementById('commercialRegistrationNumber').value = data.commercial_registration_number || '';

        const isManagerOwner = data.is_manager_owner !== false; // Default true
        document.getElementById('isManagerOwner').checked = isManagerOwner;
        toggleOwnerDetails(isManagerOwner);

        document.getElementById('ownerName').value = data.owner_name || '';
        document.getElementById('ownerPhone').value = data.owner_phone || '';

        // Tab 3: Address
        document.getElementById('showAddressInStorefront').checked = data.show_address_in_storefront || false;
        document.getElementById('useGoogleMapsLocation').checked = data.use_google_maps_location || false;
        document.getElementById('timezone').value = data.timezone || 'Asia/Riyadh';
        document.getElementById('addressCity').value = data.address_city || '';
        document.getElementById('addressStreet').value = data.address_street || '';
        document.getElementById('addressCountry').value = data.address_country || '';

        // Event Listeners
        document.getElementById('isManagerOwner').addEventListener('change', (e) => toggleOwnerDetails(e.target.checked));
        document.getElementById('commercialActivityType').addEventListener('change', updateFormFields);
        document.getElementById('electronicActivity').addEventListener('change', updateActivityTypes);

        // Initial setup
        updateFormFields();
        setupFileUploads();
        populateActivityCategories();

        // Load new commercial fields
        document.getElementById('nationalId').value = data.national_id || '';
        document.getElementById('branchesCount').value = data.branches_count || '';
        document.getElementById('employeesCount').value = data.employees_count || '';
        // Handle Activity Loading
        const savedActivity = data.electronic_activity || '';
        const savedType = data.electronic_activity_type || '';

        // Set main activity if it exists
        const mainSelect = document.getElementById('electronicActivity');
        if (savedActivity && mainSelect.querySelector(`option[value="${savedActivity}"]`)) {
            mainSelect.value = savedActivity;
        } else if (savedActivity === 'other') {
            mainSelect.value = 'other';
        }

        // Trigger update to populate types or show input
        updateActivityTypes();

        // Set type value (after updateActivityTypes handles inputs/select switching)
        const typeInput = document.getElementById('electronicActivityType');
        if (typeInput.tagName === 'SELECT') {
            if (savedType && typeInput.querySelector(`option[value="${savedType}"]`)) {
                typeInput.value = savedType;
            }
        } else {
            typeInput.value = savedType;
        }

        // Load file links (if exist)
        if (data.national_id_image) setFileLink('nationalIdImage', data.national_id_image);
        if (data.tax_certificate_image) setFileLink('taxCertificateImage', data.tax_certificate_image);
        if (data.freelance_certificate_image) setFileLink('freelanceCertificateImage', data.freelance_certificate_image);
        if (data.ecommerce_auth_certificate_image) setFileLink('ecommerceAuthCertificateImage', data.ecommerce_auth_certificate_image);
        if (data.bank_certificate_image) setFileLink('bankCertificateImage', data.bank_certificate_image);
        if (data.activity_license_image) setFileLink('activityLicenseImage', data.activity_license_image);
        if (data.commercial_registration_image_url) setFileLink('crImage', data.commercial_registration_image_url);

    } catch (error) {
        console.error('Error loading settings:', error);
        if (window.notifier) window.notifier.showToast('فشل في تحميل الإعدادات', 'error');
    }
}

function toggleOwnerDetails(isManagerOwner) {
    const section = document.getElementById('ownerDetailsSection');
    // Implementation can adjust visibility if needed based on requirements
}

function updateFormFields() {
    const type = document.getElementById('commercialActivityType').value;
    const labels = {
        individual: {
            ownerName: 'اسم المالك',
            ownerPhone: 'هاتف المالك',
            commercialName: 'الاسم التجاري'
        },
        establishment: {
            ownerName: 'اسم مالك المؤسسة',
            ownerPhone: 'هاتف مالك المؤسسة',
            commercialName: 'اسم المؤسسة'
        },
        company: {
            ownerName: 'اسم المدير العام',
            ownerPhone: 'هاتف المدير العام',
            commercialName: 'اسم الشركة'
        },
        charity: {
            ownerName: 'اسم المسؤول',
            ownerPhone: 'هاتف المسؤول',
            commercialName: 'اسم الجمعية'
        }
    };

    const current = labels[type] || labels.individual;

    document.querySelector('label[for="ownerName"]').textContent = current.ownerName;
    document.querySelector('label[for="ownerPhone"]').textContent = current.ownerPhone;
    document.querySelector('label[for="commercialName"]').textContent = current.commercialName;

    // Toggle fields based on type if needed (e.g., CR is for establishment/company)
    // For simplicity, we are just changing labels as requested initially.
}

const activityData = {
    "electronics": {
        label: "إلكترونيات (Electronics)",
        types: [
            "الهواتف الذكية وملحقاتها (Smartphones & Accessories)",
            "أجهزة محمولة وملحقاتها (Laptops & Accessories)",
            "أجهزة كهربائية وملحقاتها (Electrical Appliances & Accessories)",
            "الكاميرات ومستلزمات التصوير (Cameras & Photography Gear)",
            "كاميرات المراقبة (Security Cameras)"
        ]
    },
    "food": {
        label: "أطعمة (Food)",
        types: [
            "مطاعم ومقاهي (Restaurants & Cafes)",
            "مخابز وحلويات (Bakeries & Sweets)",
            "تمور وعسل (Dates & Honey)",
            "قهوة وشاي (Coffee & Tea)",
            "بهارات وتوابل (Spices & Seasonings)",
            "لحوم ودواجن طازجة (Fresh Meat & Poultry)",
            "فواكه وخضروات (Fruits & Vegetables)",
            "أغذية صحية وعضوية (Healthy & Organic Food)",
            "أسر منتجة (Home Business Food)",
            "تموين وسوبر ماركت (Groceries)"
        ]
    },
    "perfumes": {
        label: "العطورات (Perfumes)",
        types: [
            "عطور شرقية ودهن العود (Oriental Perfumes & Oud)",
            "عطور فرنسية وعالمية (French & International Perfumes)",
            "بخور ومعمول (Incense)",
            "زيوت عطرية (Essential Oils)",
            "معطرات جو ومفارش (Home & Linen Scents)",
            "مسك وعنبر (Musk & Amber)"
        ]
    },
    "fashion": {
        label: "أزياء ومجوهرات (Fashion & Jewelry)",
        types: [
            "ملابس نسائية (Women's Clothing)",
            "ملابس رجالية (Men's Clothing)",
            "ملابس أطفال ومواليد (Kids & Baby Clothing)",
            "عبايات وجلابيات (Abayas & Jalabiyas)",
            "أحذية (Shoes)",
            "حقائب وإكسسوارات جلدية (Bags & Leather Goods)",
            "ذهب ومجوهرات (Gold & Jewelry)",
            "ساعات (Watches)",
            "ملابس رياضية (Sportswear)",
            "أقمشة ومنسوجات (Fabrics & Textiles)"
        ]
    },
    "beauty": {
        label: "عناية وتجميل (Care & Beauty)",
        types: [
            "مكياج وأدوات تجميل (Makeup & Tools)",
            "عناية بالبشرة (Skin Care)",
            "عناية بالشعر (Hair Care)",
            "عناية شخصية ونظافة (Personal Care & Hygiene)",
            "عدسات لاصقة (Contact Lenses)",
            "أجهزة العناية الشخصية (Personal Care Appliances)",
            "صابون طبيعي ومنتجات سبا (Natural Soap & Spa)"
        ]
    },
    "gifts": {
        label: "هدايا وحفلات (Gifts & Parties)",
        types: [
            "تغليف هدايا (Gift Wrapping)",
            "زهور ونباتات طبيعية (Flowers & Plants)",
            "بطاقات تهنئة (Greeting Cards)",
            "توزيعات مناسبات (Event Giveaways)",
            "تجهيز حفلات وأعياد ميلاد (Party Supplies)",
            "هدايا شركات ودعاية (Corporate Gifts)"
        ]
    },
    "stationery": {
        label: "مستلزمات مكتبية وقرطاسية (Office Supplies & Stationery)",
        types: [
            "أدوات مدرسية (School Supplies)",
            "أدوات مكتبية (Office Supplies)",
            "طابعات وأحبار (Printers & Ink)",
            "أدوات رسم وفنون (Art Supplies)",
            "دفاتر ومذكرات (Notebooks & Diaries)"
        ]
    },
    "health": {
        label: "الصحة والعلاج (Health & Therapy)",
        types: [
            "أدوية وصفات طبية (Medicines)",
            "مكملات غذائية وفيتامينات (Supplements & Vitamins)",
            "مستلزمات طبية وأجهزة (Medical Equipment)",
            "نظارات وبصريات (Optics & Glasses)",
            "مستحضرات تجميل طبية (Derma Cosmetics)"
        ]
    },
    "home": {
        label: "احتياجات المنزل والحدائق (Home & Garden Needs)",
        types: [
            "أثاث ومفروشات (Furniture)",
            "ديكور وإكسسوارات منزلية (Home Decor)",
            "أدوات مطبخ ومائدة (Kitchenware & Dining)",
            "إضاءة وكهرباء (Lighting & Electrical)",
            "أدوات تنظيف ومنظفات (Cleaning Supplies)",
            "زراعة وبذور (Agriculture & Seeds)",
            "معدات وأدوات يدوية (Tools & Hardware)"
        ]
    },
    "sports": {
        label: "الرياضة والألعاب والتخييم (Sports, Games & Camping)",
        types: [
            "أجهزة ومعدات رياضية (Gym Equipment)",
            "ألعاب فيديو وإلكترونيات (Video Games & Consoles)",
            "ألعاب أطفال تعليمية (Kids Educational Toys)",
            "ألعاب لوحية وجماعية (Board Games)",
            "لوازم رحلات وتخييم (Camping & Hiking Gear)",
            "دراجات هوائية وسكوتر (Bicycles & Scooters)"
        ]
    },
    "pets": {
        label: "مستلزمات حيوانات اليفة (Pet Supplies)",
        types: [
            "طعام حيوانات (Pet Food)",
            "إكسسوارات وألعاب حيوانات (Pet Accessories & Toys)",
            "رمل ومستلزمات نظافة (Litter & Cleaning)",
            "أقفاص وبيوت (Cages & Houses)",
            "بيطرة وعناية صحية (Veterinary Care)"
        ]
    },
    "vehicles": {
        label: "المركبات (Vehicles)",
        types: [
            "قطع غيار سيارات (Auto Spare Parts)",
            "إكسسوارات وزينة سيارات (Car Accessories)",
            "إطارات وجنوط (Tires & Rims)",
            "زيوت وسوائل (Oils & Fluids)",
            "أدوات العناية والغسيل (Car Care & Wash Tools)"
        ]
    },
    "culture": {
        label: "ثقافة وفنون (Culture & Arts)",
        types: [
            "كتب وروايات (Books & Novels)",
            "لوحات فنية ومجسمات (Art Pieces & Sculptures)",
            "آلات موسيقية (Musical Instruments)",
            "حرف يدوية وتراثية (Handicrafts)",
            "دورات تعليمية (Educational Courses)"
        ]
    },
    "services": {
        label: "الخدمات (Services)",
        types: [
            "تصميم وجرافيك (Design & Graphics)",
            "تسويق إلكتروني (Digital Marketing)",
            "استشارات (Consulting)",
            "صيانة وتشغيل (Maintenance Services)",
            "حجوزات وسفر (Travel & Booking)",
            "طباعة وتصوير (Printing Services)"
        ]
    },
    "clubs": {
        label: "الأندية الرياضية (Sports Clubs)",
        types: [
            "أندية لياقة بدنية (Fitness Gyms)",
            "أكاديميات كرة قدم (Football Academies)",
            "مراكز فنون قتالية (Martial Arts Centers)",
            "تعليم سباحة (Swimming Classes)",
            "يوغا وبيلاتس (Yoga & Pilates)"
        ]
    },
    "other": {
        label: "اخرى (Other)",
        types: []
    }
};

function populateActivityCategories() {
    const mainSelect = document.getElementById('electronicActivity');
    mainSelect.innerHTML = '<option value="">اختر النشاط...</option>';

    for (const [key, data] of Object.entries(activityData)) {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = data.label;
        mainSelect.appendChild(option);
    }
}

function updateActivityTypes() {
    const mainSelect = document.getElementById('electronicActivity');
    const selectedKey = mainSelect.value;
    const typeContainer = document.getElementById('electronicActivityType').parentElement;
    const oldInput = document.getElementById('electronicActivityType');

    // Clear old label or ensure it's correct
    const label = typeContainer.querySelector('.form-label');
    label.textContent = 'نوع النشاط';

    if (selectedKey === 'other') {
        // Switch to Input
        if (oldInput.tagName !== 'INPUT') {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
            input.id = 'electronicActivityType';
            input.placeholder = 'أدخل نوع النشاط...';
            oldInput.replaceWith(input);
        }
        // Force display block for label if obscured? No, bootstrap handles.
    } else {
        // Switch to Select
        let select = oldInput;
        if (oldInput.tagName !== 'SELECT') {
            select = document.createElement('select');
            select.className = 'form-select';
            select.id = 'electronicActivityType';
            oldInput.replaceWith(select);
        }

        // Populate Select
        select.innerHTML = '<option value="">اختر النوع...</option>';
        if (activityData[selectedKey]) {
            activityData[selectedKey].types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                select.appendChild(option);
            });
        }
    }
}


function setupFileUploads() {
    document.querySelectorAll('.file-upload-input').forEach(input => {
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                // Show loading state
                const btn = e.target.parentElement.querySelector('.upload-btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                btn.disabled = true;

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Upload failed');

                const data = await response.json();

                // Update hidden input with URL
                const fieldName = input.dataset.field;
                document.getElementById(fieldName).value = data.url;

                // Update UI to show success/link
                setFileLink(fieldName, data.url);

                if (window.notifier) window.notifier.showToast('تم رفع الملف بنجاح', 'success');

            } catch (error) {
                console.error('Upload error:', error);
                if (window.notifier) window.notifier.showToast('فشل رفع الملف', 'error');
            } finally {
                const btn = e.target.parentElement.querySelector('.upload-btn');
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    });
}

function setFileLink(elementId, url) {
    // Check if link container exists, if not create it
    const input = document.getElementById(elementId); // The hidden input
    if (!input) return;

    const container = input.closest('.file-upload-container');
    let link = container.querySelector('.file-link');

    if (url) {
        if (!link) {
            link = document.createElement('a');
            link.className = 'd-block mt-2 text-primary text-decoration-none file-link';
            link.target = '_blank';
            container.appendChild(link);
        }
        link.href = url;
        link.innerHTML = '<i class="fa-solid fa-file-arrow-down me-1"></i> عرض الملف المرفق';
    }
}

async function saveSettings() {
    const btn = document.getElementById('saveBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    const payload = {
        // Tab 1
        store_name: document.getElementById('storeName').value,
        support_email: document.getElementById('supportEmail').value,
        support_phone: document.getElementById('supportPhone').value,

        // Tab 2
        commercial_activity_type: document.getElementById('commercialActivityType').value,
        commercial_name: document.getElementById('commercialName').value,
        commercial_registration_name: document.getElementById('commercialRegistrationName').value,
        commercial_registration_number: document.getElementById('commercialRegistrationNumber').value,
        is_manager_owner: document.getElementById('isManagerOwner').checked,
        owner_name: document.getElementById('ownerName').value,
        owner_phone: document.getElementById('ownerPhone').value,
        national_id: document.getElementById('nationalId').value,
        branches_count: document.getElementById('branchesCount').value ? parseInt(document.getElementById('branchesCount').value) : null,
        employees_count: document.getElementById('employeesCount').value ? parseInt(document.getElementById('employeesCount').value) : null,
        electronic_activity: document.getElementById('electronicActivity').value,
        electronic_activity_type: document.getElementById('electronicActivityType').value,

        // File URLs (Hidden inputs)
        national_id_image: document.getElementById('nationalIdImage').value,
        tax_certificate_image: document.getElementById('taxCertificateImage').value,
        freelance_certificate_image: document.getElementById('freelanceCertificateImage').value,
        ecommerce_auth_certificate_image: document.getElementById('ecommerceAuthCertificateImage').value,
        bank_certificate_image: document.getElementById('bankCertificateImage').value,
        activity_license_image: document.getElementById('activityLicenseImage').value,
        commercial_registration_image_url: document.getElementById('crImage').value,

        // Tab 3
        show_address_in_storefront: document.getElementById('showAddressInStorefront').checked,
        use_google_maps_location: document.getElementById('useGoogleMapsLocation').checked,
        timezone: document.getElementById('timezone').value,
        address_city: document.getElementById('addressCity').value,
        address_street: document.getElementById('addressStreet').value,
        address_country: document.getElementById('addressCountry').value
    };

    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save');

        if (window.notifier) window.notifier.showToast('تم حفظ الإعدادات بنجاح', 'success');

    } catch (error) {
        console.error('Error saving settings:', error);
        if (window.notifier) window.notifier.showToast('فشل في حفظ الإعدادات', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}
