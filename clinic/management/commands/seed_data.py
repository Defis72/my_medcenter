from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta, time
from decimal import Decimal
import random
import os
import base64
from django.core.files.base import ContentFile
from clinic.avatar_data import DOCTOR_AVATARS, CONTACT_AVATARS, ARTICLE_IMAGES

from clinic.models import (
    CompanyInfo, CompanyHistory, Article, GlossaryTerm, Contact,
    Vacancy, Review, PromoCode, Specialization, Department,
    DoctorCategory, Doctor, ServiceCategory, Service, Client,
    Diagnosis, ClientDiagnosis, Schedule, Appointment, Sale
)




class Command(BaseCommand):
    help = 'Seed the database with demo data (>=10 records per table)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # ── Superuser ──────────────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@medcenter.by', 'admin123')
            self.stdout.write('  Created superuser admin / admin123')

        # ── Company ────────────────────────────────────────────────────────
        company, _ = CompanyInfo.objects.get_or_create(
            name='МедЦентр Здоровье',
            defaults={
                'description': 'Современный медицинский центр с полным спектром услуг. Здоровье каждого пациента — наш главный приоритет.',
                'address': 'г. Минск, ул. Независимости, 100',
                'phone': '+375 (29) 100-00-01',
                'email': 'info@medcenter.by',
                'founded_year': 2010,
            }
        )

        history_entries = [
            (2010, 'Основание медицинского центра'),
            (2012, 'Открытие отделения кардиологии'),
            (2014, 'Получение лицензии на хирургическую деятельность'),
            (2016, 'Внедрение электронной записи к врачам'),
            (2018, 'Открытие современной лаборатории'),
            (2020, 'Запуск телемедицины в период пандемии'),
            (2022, 'Приобретение МРТ нового поколения'),
            (2023, 'Открытие педиатрического отделения'),
            (2024, 'Внедрение ИИ-диагностики'),
            (2025, 'Расширение: открытие второго корпуса'),
        ]
        for year, event in history_entries:
            CompanyHistory.objects.get_or_create(
                company=company, year=year, defaults={'event': event})

        # ── Articles (>=10) ───────────────────────────────────────────────
        articles_data = [
            ('Профилактика гриппа и ОРВИ',
             'Как защититься от сезонных вирусных инфекций',
             'Грипп и ОРВИ — самые распространённые инфекционные заболевания. Ежегодная вакцинация снижает риск заражения на 60-90%. Также важно соблюдать гигиену рук, проветривать помещения и укреплять иммунитет.'),
            ('Как подготовиться к МРТ',
             'Всё о процедуре МРТ: подготовка и результаты',
             'МРТ — безопасная и информативная процедура. Перед исследованием необходимо снять металлические предметы. Длительность — 20-60 минут. Результаты готовы в течение суток.'),
            ('Вакцинация: мифы и реальность',
             'Разбираем популярные мифы о прививках',
             'Вакцинация — один из самых эффективных способов защиты от инфекций. Современные вакцины проходят многолетние испытания и абсолютно безопасны для большинства людей.'),
            ('Диабет 2 типа: управление и профилактика',
             'Как контролировать уровень сахара в крови',
             'Сахарный диабет 2 типа поддаётся контролю при правильном питании и физической активности. Регулярный мониторинг глюкозы — залог здоровья диабетика.'),
            ('Новые технологии в диагностике',
             'Наш центр получил современное оборудование',
             'В этом году мы приобрели томограф нового поколения, позволяющий выявлять патологии с точностью до 0,5 мм. Теперь диагностика стала быстрее и точнее.'),
            ('Здоровое сердце: советы кардиолога',
             'Как сохранить сердечно-сосудистую систему здоровой',
             'Регулярные умеренные физические нагрузки, сбалансированное питание и отказ от курения — три кита здоровья сердца. Контролируйте артериальное давление и холестерин.'),
            ('Правильное питание при гипертонии',
             'Диета, снижающая давление без таблеток',
             'Диета DASH доказала эффективность в снижении давления. Ограничьте соль до 5 г в сутки, увеличьте потребление калия (бананы, курага) и откажитесь от алкоголя.'),
            ('Детский медосмотр: зачем и когда',
             'Плановые осмотры ребёнка по возрасту',
             'Профилактические осмотры помогают выявить отклонения на ранней стадии. В нашем центре работают опытные педиатры и узкие специалисты для детей.'),
            ('Остеохондроз: лечение и профилактика',
             'Как уберечь позвоночник от разрушения',
             'Остеохондроз — дегенеративное заболевание дисков позвоночника. Лечебная физкультура, массаж и физиотерапия значительно замедляют прогрессирование болезни.'),
            ('Сезонная аллергия: как пережить',
             'Рекомендации аллерголога на период цветения',
             'В период цветения закрывайте окна в ветреную погоду, принимайте назначенные антигистаминные препараты и носите солнцезащитные очки на улице.'),
            ('УЗИ щитовидной железы: кому нужно',
             'Показания и результаты ультразвукового исследования ЩЖ',
             'УЗИ щитовидной железы рекомендуется всем после 40 лет, а также при наличии жалоб на усталость, изменение веса или нарушения сна.'),
        ]
        for aidx, (title, summary, content_text) in enumerate(articles_data):
            article, acreated = Article.objects.get_or_create(
                title=title, defaults={'summary': summary, 'content': content_text, 'is_published': True})
            if not article.image_data:
                key = f'article_{aidx+1:02d}'
                if key in ARTICLE_IMAGES:
                    article.image_data = ARTICLE_IMAGES[key]
                    article.save(update_fields=['image_data'])

        # ── Glossary (>=10) ───────────────────────────────────────────────
        terms_data = [
            ('Что такое МРТ?', 'МРТ (магнитно-резонансная томография) — метод медицинской визуализации, основанный на использовании магнитного поля и радиоволн.'),
            ('Что такое УЗИ?', 'УЗИ (ультразвуковое исследование) — метод диагностики, использующий ультразвуковые волны для визуализации внутренних органов.'),
            ('Как записаться на приём?', 'Записаться можно онлайн через наш сайт в личном кабинете, по телефону +375 (29) 100-00-01 или лично в регистратуре.'),
            ('Какие документы нужны для первого посещения?', 'При первом визите предъявите паспорт гражданина Республики Беларусь и страховой полис при наличии.'),
            ('Что такое ОАК?', 'ОАК — общий анализ крови. Базовое лабораторное исследование, оценивающее состав и свойства крови.'),
            ('Как подготовиться к анализу крови?', 'Анализ крови сдаётся натощак, не менее 8-12 часов после последнего приёма пищи. Воду пить можно.'),
            ('Что такое ЭКГ?', 'ЭКГ (электрокардиограмма) — метод регистрации электрической активности сердца. Позволяет выявить аритмии и ишемию.'),
            ('Как часто нужно проходить диспансеризацию?', 'Взрослым рекомендуется проходить диспансеризацию раз в год. Включает осмотр терапевта и базовые анализы.'),
            ('Что входит в общий анализ мочи?', 'ОАМ оценивает цвет, прозрачность, pH, плотность мочи, а также наличие белка, глюкозы, лейкоцитов и эритроцитов.'),
            ('Можно ли отменить запись онлайн?', 'Да, отменить или перенести запись можно в личном кабинете на сайте или позвонив в регистратуру не позднее чем за 2 часа.'),
            ('Что такое биохимический анализ крови?', 'Биохимический анализ крови оценивает работу внутренних органов: печени, почек, поджелудочной железы, а также уровень холестерина и глюкозы.'),
        ]
        for question, answer in terms_data:
            GlossaryTerm.objects.get_or_create(question=question, defaults={'answer': answer})

        # ── Contacts (>=10) ───────────────────────────────────────────────
        contacts_data = [
            ('Иванова Мария Петровна', 'Главный врач', '+375 (29) 100-00-01', 'ivanova@medcenter.by', 0, 'contact_01'),
            ('Петров Сергей Иванович', 'Заместитель по лечебной части', '+375 (29) 100-00-02', 'petrov@medcenter.by', 1, 'contact_02'),
            ('Сидорова Анна Николаевна', 'Заведующая регистратурой', '+375 (29) 100-00-03', 'sidorova@medcenter.by', 2, 'contact_03'),
            ('Кузнецов Дмитрий Алексеевич', 'Начальник отдела кадров', '+375 (29) 100-00-04', 'kuznetsov@medcenter.by', 3, 'contact_04'),
            ('Романова Елена Владимировна', 'Главная медицинская сестра', '+375 (29) 100-00-05', 'romanova@medcenter.by', 4, 'contact_05'),
            ('Новиков Андрей Сергеевич', 'Заведующий лабораторией', '+375 (33) 100-00-06', 'novikov@medcenter.by', 5, 'contact_06'),
            ('Козлова Татьяна Ивановна', 'Бухгалтер', '+375 (44) 100-00-07', 'kozlova@medcenter.by', 6, 'contact_07'),
            ('Морозов Виктор Николаевич', 'Системный администратор', '+375 (29) 100-00-08', 'morozov@medcenter.by', 7, 'contact_08'),
            ('Лебедева Ольга Александровна', 'Менеджер по качеству', '+375 (33) 100-00-09', 'lebedeva@medcenter.by', 8, 'contact_09'),
            ('Федоров Игорь Павлович', 'Пресс-секретарь', '+375 (44) 100-00-10', 'fedorov@medcenter.by', 9, 'contact_10'),
        ]
        for cidx, (name, pos, phone, email, order, photo_key) in enumerate(contacts_data):
            contact, ccreated = Contact.objects.get_or_create(full_name=name, defaults={
                'position': pos, 'phone': phone, 'email': email, 'order': order})
            if not contact.photo_data:
                key = f'contact_{cidx+1:02d}'
                if key in CONTACT_AVATARS:
                    contact.photo_data = CONTACT_AVATARS[key]
                    contact.save(update_fields=['photo_data'])

        # ── Vacancies (>=10) ──────────────────────────────────────────────
        vacancies_data = [
            ('Врач-терапевт', 'Требуется врач-терапевт с опытом работы от 3 лет. Высшее медицинское образование обязательно. График 5/2, полная занятость.', 2500, 3500),
            ('Медицинская сестра', 'Требуется медицинская сестра на терапевтическое отделение. Опыт от 1 года. График сменный.', 1200, 1800),
            ('Врач-рентгенолог', 'Ищем специалиста с опытом работы с КТ и МРТ не менее 2 лет. Официальное трудоустройство.', 3000, 4000),
            ('Администратор ресепшн', 'Требуется администратор. Знание ПК и 1С, грамотная речь, стрессоустойчивость. График 2/2.', 900, 1200),
            ('Врач-кардиолог', 'Опыт работы от 5 лет. Знание ЭхоКГ обязательно. Высокая заработная плата + бонусы.', 3500, 5000),
            ('Санитар', 'Без опыта работы. Обучение за счёт работодателя. Полный соцпакет.', 700, 900),
            ('Врач-невролог', 'Приглашаем невролога со стажем от 3 лет. Работа с современным оборудованием.', 3000, 4500),
            ('Медицинский лаборант', 'Опыт работы в лаборатории от 1 года. Знание автоматических анализаторов приветствуется.', 1300, 1700),
            ('Врач-офтальмолог', 'Полная занятость, совместительство возможно. Наличие сертификата обязательно.', 2800, 3800),
            ('Фельдшер скорой помощи', 'Опыт работы на скорой от 2 лет. Наличие водительского удостоверения приветствуется.', 1800, 2500),
            ('Дерматолог-косметолог', 'Опыт инъекционной косметологии обязателен. Наработанная клиентская база приветствуется.', 3200, 4800),
        ]
        for title, desc, s_from, s_to in vacancies_data:
            Vacancy.objects.get_or_create(title=title, defaults={
                'description': desc, 'salary_from': s_from, 'salary_to': s_to})

        # ── Promo codes (>=10) ────────────────────────────────────────────
        today = date.today()
        promos = [
            ('HEALTH10', 'Скидка 10% на первый приём', 10, today, today + timedelta(days=60), True),
            ('SENIOR15', 'Скидка 15% для пенсионеров', 15, today - timedelta(days=10), today + timedelta(days=30), True),
            ('SUMMER20', 'Летняя скидка 20% (архив)', 20, today - timedelta(days=90), today - timedelta(days=1), False),
            ('FAMILY25', 'Семейный пакет — скидка 25%', 25, today, today + timedelta(days=90), True),
            ('BIRTHDAY30', 'Скидка 30% в день рождения', 30, today, today + timedelta(days=365), True),
            ('LAB5', 'Скидка 5% на лабораторные анализы', 5, today, today + timedelta(days=120), True),
            ('ONLINE12', 'Скидка 12% при онлайн-записи', 12, today, today + timedelta(days=45), True),
            ('STUDENT10', 'Скидка 10% для студентов', 10, today, today + timedelta(days=180), True),
            ('AUTUMN15', 'Осенняя акция 15%', 15, today - timedelta(days=30), today + timedelta(days=30), True),
            ('VIP20', 'VIP-скидка постоянным клиентам', 20, today, today + timedelta(days=365), True),
            ('FIRSTVISIT8', 'Скидка 8% на первое посещение', 8, today, today + timedelta(days=60), True),
        ]
        for code, desc, disc, vf, vt, active in promos:
            PromoCode.objects.get_or_create(code=code, defaults={
                'description': desc, 'discount_percent': disc,
                'valid_from': vf, 'valid_to': vt, 'is_active': active})

        # ── Specializations ───────────────────────────────────────────────
        specs = ['Терапевт', 'Кардиолог', 'Невролог', 'Хирург', 'Офтальмолог',
                 'Дерматолог', 'Эндокринолог', 'Ортопед', 'Аллерголог', 'Педиатр']
        spec_objs = {}
        for s in specs:
            obj, _ = Specialization.objects.get_or_create(name=s)
            spec_objs[s] = obj

        # ── Departments ───────────────────────────────────────────────────
        depts_data = [
            ('Терапевтическое', 1), ('Кардиологическое', 2), ('Неврологическое', 2),
            ('Хирургическое', 3), ('Офтальмологическое', 1), ('Дерматологическое', 1),
            ('Эндокринологическое', 2), ('Ортопедическое', 3), ('Лабораторное', 0), ('Педиатрическое', 1),
        ]
        dept_objs = {}
        for name, floor in depts_data:
            obj, _ = Department.objects.get_or_create(name=name, defaults={'floor': floor})
            dept_objs[name] = obj

        # ── Doctor categories ─────────────────────────────────────────────
        cats_data = ['Высшая категория', 'Первая категория', 'Вторая категория', 'Без категории']
        cat_objs = {}
        for c in cats_data:
            obj, _ = DoctorCategory.objects.get_or_create(name=c)
            cat_objs[c] = obj

        # ── Doctors (>=10) ────────────────────────────────────────────────
        doctors_data = [
            ('dr_ivanov',   'doctor123', 'Иван',      'Иванов',    'Петрович',   date(1975, 3, 15),  '+375 (29) 200-00-01', 'ivanov@medcenter.by',   'Терапевт',        'Высшая категория',  'Терапевтическое',     20),
            ('dr_petrova',  'doctor123', 'Светлана',  'Петрова',   'Ивановна',   date(1980, 7, 22),  '+375 (29) 200-00-02', 'petrova@medcenter.by',  'Кардиолог',       'Высшая категория',  'Кардиологическое',    15),
            ('dr_sidorov',  'doctor123', 'Алексей',   'Сидоров',   'Викторович', date(1978, 11, 5),  '+375 (33) 200-00-03', 'sidorov@medcenter.by',  'Невролог',        'Первая категория',  'Неврологическое',     18),
            ('dr_kozlova',  'doctor123', 'Наталья',   'Козлова',   'Сергеевна',  date(1985, 2, 28),  '+375 (44) 200-00-04', 'kozlova@medcenter.by',  'Хирург',          'Первая категория',  'Хирургическое',       12),
            ('dr_novikov',  'doctor123', 'Дмитрий',   'Новиков',   'Александрович', date(1970, 9, 10), '+375 (29) 200-00-05', 'novikov@medcenter.by', 'Офтальмолог',    'Высшая категория',  'Офтальмологическое',  25),
            ('dr_romanova', 'doctor123', 'Екатерина', 'Романова',  'Николаевна', date(1983, 4, 17),  '+375 (33) 200-00-06', 'romanova@medcenter.by', 'Дерматолог',      'Первая категория',  'Дерматологическое',   13),
            ('dr_fedorov',  'doctor123', 'Игорь',     'Фёдоров',   'Павлович',   date(1977, 8, 30),  '+375 (44) 200-00-07', 'fedorov@medcenter.by',  'Эндокринолог',    'Высшая категория',  'Эндокринологическое', 17),
            ('dr_morozov',  'doctor123', 'Виктор',    'Морозов',   'Дмитриевич', date(1982, 6, 14),  '+375 (29) 200-00-08', 'morozov@medcenter.by',  'Ортопед',         'Вторая категория',  'Ортопедическое',      10),
            ('dr_lebedeva', 'doctor123', 'Ольга',     'Лебедева',  'Андреевна',  date(1990, 1, 25),  '+375 (33) 200-00-09', 'lebedeva@medcenter.by', 'Аллерголог',      'Вторая категория',  'Терапевтическое',     7),
            ('dr_volkov',   'doctor123', 'Сергей',    'Волков',    'Игоревич',   date(1988, 12, 3),  '+375 (44) 200-00-10', 'volkov@medcenter.by',   'Педиатр',         'Первая категория',  'Педиатрическое',      9),
        ]
        doctor_objs = []
        for idx, (uname, pwd, fn, ln, pat, dob, phone, email, spec_name, cat_name, dept_name, exp) in enumerate(doctors_data):
            u, ucreated = User.objects.get_or_create(
                username=uname,
                defaults={'first_name': fn, 'last_name': ln, 'email': email})
            if ucreated:
                u.set_password(pwd)
                u.save()
            doc, created = Doctor.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fn, 'last_name': ln, 'patronymic': pat,
                    'date_of_birth': dob, 'phone': phone,
                    'category': cat_objs[cat_name],
                    'department': dept_objs[dept_name],
                    'experience_years': exp, 'user': u,
                })
            if created:
                doc.specializations.add(spec_objs[spec_name])
            # Save base64 avatar directly into DB field (no filesystem needed)
            if not doc.photo_data and uname in DOCTOR_AVATARS:
                doc.photo_data = DOCTOR_AVATARS[uname]
                doc.save(update_fields=['photo_data'])
            doctor_objs.append(doc)
        self.stdout.write(f'  Doctors: {len(doctor_objs)}')

        # ── Service categories & Services (>=10) ──────────────────────────
        svc_cats = {
            'Консультации':        ServiceCategory.objects.get_or_create(name='Консультации')[0],
            'Лабораторные анализы': ServiceCategory.objects.get_or_create(name='Лабораторные анализы')[0],
            'Лечебные процедуры':  ServiceCategory.objects.get_or_create(name='Лечебные процедуры')[0],
            'Диагностика':         ServiceCategory.objects.get_or_create(name='Диагностика')[0],
            'Физиотерапия':        ServiceCategory.objects.get_or_create(name='Физиотерапия')[0],
        }
        services_data = [
            ('Консультации',       'Первичный приём терапевта',       35.00, 30),
            ('Консультации',       'Повторный приём терапевта',        25.00, 20),
            ('Консультации',       'Консультация кардиолога',          50.00, 40),
            ('Консультации',       'Консультация невролога',           50.00, 40),
            ('Консультации',       'Консультация офтальмолога',        45.00, 35),
            ('Лабораторные анализы', 'Общий анализ крови',            12.00, 10),
            ('Лабораторные анализы', 'Биохимия крови',                25.00, 10),
            ('Лабораторные анализы', 'Общий анализ мочи',             10.00, 10),
            ('Лабораторные анализы', 'Анализ на гормоны щитовидки',   35.00, 10),
            ('Лечебные процедуры', 'Внутримышечная инъекция',          8.00, 10),
            ('Лечебные процедуры', 'Капельница',                      30.00, 60),
            ('Диагностика',        'ЭКГ',                             20.00, 20),
            ('Диагностика',        'УЗИ брюшной полости',             45.00, 30),
            ('Диагностика',        'УЗИ щитовидной железы',           40.00, 25),
            ('Физиотерапия',       'Магнитотерапия',                  18.00, 20),
            ('Физиотерапия',       'Электрофорез',                    15.00, 20),
        ]
        svc_objs = []
        for cat_name, svc_name, price, dur in services_data:
            svc, _ = Service.objects.get_or_create(
                name=svc_name,
                defaults={'category': svc_cats[cat_name],
                          'price': Decimal(str(price)),
                          'duration_minutes': dur,
                          'description': f'Профессиональная услуга: {svc_name}.'})
            svc_objs.append(svc)
        self.stdout.write(f'  Services: {len(svc_objs)}')

        # ── Clients (>=10) ────────────────────────────────────────────────
        clients_data = [
            ('client_petrov',   'client123', 'Пётр',      'Петров',    'Васильевич',  date(1985, 6, 15), '+375 (29) 300-00-01', 'petrov_p@mail.by',    'г. Минск, ул. Ленина, 5-10'),
            ('client_kozlov',   'client123', 'Андрей',    'Козлов',    'Иванович',    date(1990, 3, 22), '+375 (33) 300-00-02', 'kozlov_a@mail.by',    'г. Минск, ул. Советская, 12-3'),
            ('client_sorokina', 'client123', 'Людмила',   'Сорокина',  'Петровна',    date(1978, 9, 10), '+375 (44) 300-00-03', 'sorokina_l@mail.by',  'г. Минск, пр. Победителей, 7-15'),
            ('client_voronov',  'client123', 'Вячеслав',  'Воронов',   'Николаевич',  date(1965, 12, 5), '+375 (29) 300-00-04', 'voronov_v@mail.by',   'г. Минск, ул. Притыцкого, 33-45'),
            ('client_zakharova','client123', 'Ирина',     'Захарова',  'Михайловна',  date(1988, 4, 21), '+375 (29) 300-00-05', 'zakharova_i@mail.by', 'г. Минск, ул. Якуба Коласа, 2-8'),
            ('client_zaitseva', 'client123', 'Марина',    'Зайцева',   'Петровна',    date(1991, 10, 15),'+375 (33) 300-00-06', 'zaitseva_m@mail.by',  'г. Минск, ул. Сурганова, 19-22'),
            ('client_nikitin',  'client123', 'Николай',   'Никитин',   'Сергеевич',   date(1972, 7, 8),  '+375 (44) 300-00-07', 'nikitin_n@mail.by',   'г. Минск, пр. Независимости, 88-14'),
            ('client_orlova',   'client123', 'Валентина', 'Орлова',    'Ивановна',    date(1955, 2, 14), '+375 (29) 300-00-08', 'orlova_v@mail.by',    'г. Минск, ул. Немига, 3-5'),
            ('client_stepanov', 'client123', 'Артём',     'Степанов',  'Дмитриевич',  date(1995, 5, 30), '+375 (33) 300-00-09', 'stepanov_a@mail.by',  'г. Минск, ул. Кальварийская, 55-6'),
            ('client_grigorieva','client123', 'Наталья',  'Григорьева','Олеговна',    date(1983, 8, 18), '+375 (44) 300-00-10', 'grigorieva_n@mail.by','г. Минск, ул. Куйбышева, 10-1'),
            ('client_fedosov',  'client123', 'Алексей',   'Федосов',   'Романович',   date(2001, 1, 3),  '+375 (29) 300-00-11', 'fedosov_a@mail.by',   'г. Минск, ул. Маяковского, 77-33'),
            ('client_larionova','client123', 'Галина',    'Ларионова', 'Владимировна',date(1969, 11, 27),'+375 (33) 300-00-12', 'larionova_g@mail.by', 'г. Минск, пр. Рокоссовского, 44-21'),
        ]
        client_objs = []
        for uname, pwd, fn, ln, pat, dob, phone, email, addr in clients_data:
            u, ucreated = User.objects.get_or_create(
                username=uname, defaults={'first_name': fn, 'last_name': ln, 'email': email})
            if ucreated:
                u.set_password(pwd)
                u.save()
            cl, _ = Client.objects.get_or_create(
                email=email,
                defaults={'first_name': fn, 'last_name': ln, 'patronymic': pat,
                          'date_of_birth': dob, 'phone': phone,
                          'address': addr, 'user': u})
            client_objs.append(cl)
        self.stdout.write(f'  Clients: {len(client_objs)}')

        # ── Diagnoses (>=10) ──────────────────────────────────────────────
        diagnoses_data = [
            ('J06', 'ОРВИ', 'Острая респираторная вирусная инфекция'),
            ('I10', 'Гипертония', 'Эссенциальная (первичная) гипертензия'),
            ('E11', 'Диабет 2 типа', 'Сахарный диабет 2 типа без осложнений'),
            ('M54', 'Дорсалгия', 'Боль в спине, остеохондроз позвоночника'),
            ('K21', 'ГЭРБ', 'Гастроэзофагеальный рефлюкс'),
            ('J45', 'Астма', 'Бронхиальная астма'),
            ('H52', 'Аномалия рефракции', 'Миопия, гиперметропия, астигматизм'),
            ('G43', 'Мигрень', 'Мигрень с аурой и без'),
            ('L20', 'Дерматит', 'Атопический дерматит'),
            ('E03', 'Гипотиреоз', 'Гипотиреоз неуточнённый'),
        ]
        diag_objs = []
        for code, name, desc in diagnoses_data:
            d, _ = Diagnosis.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
            diag_objs.append(d)

        # ── Reviews (>=10) ────────────────────────────────────────────────
        reviews_data = [
            ('Петров Пётр', 5, 'Отличный медицинский центр! Врачи внимательные, оборудование современное. Очень доволен обслуживанием.'),
            ('Козлова Марина', 5, 'Записалась к кардиологу, всё прошло на высшем уровне. Доктор очень грамотный, всё объяснил подробно.'),
            ('Сидоренко Виктор', 4, 'Хороший центр, но приходится ждать в очереди. Врачи профессиональные, анализы быстро.'),
            ('Романова Ольга', 5, 'Обслуживание на отлично! Приятная атмосфера, вежливый персонал. Рекомендую всем знакомым.'),
            ('Кузнецов Андрей', 4, 'Неплохое место, цены адекватные. Запись через сайт очень удобная, не нужно звонить.'),
            ('Захарова Ирина', 5, 'Прекрасный центр! Прошла полное обследование за один день. Результаты получила быстро.'),
            ('Воронов Дмитрий', 3, 'В целом неплохо, но хотелось бы более удобную парковку. Качество медицинской помощи хорошее.'),
            ('Степанова Наталья', 5, 'Очень благодарна врачу-неврологу! Наконец-то нашла причину своих головных болей.'),
            ('Никитин Сергей', 4, 'Хорошая лаборатория, анализы готовы в день сдачи. Цены чуть выше средних, но качество того стоит.'),
            ('Орлова Галина', 5, 'Обратилась с проблемой кожи — дерматолог назначил правильное лечение, уже через 2 недели результат!'),
            ('Федосов Алексей', 4, 'Удобное расположение в центре города, хорошие специалисты. Буду обращаться ещё.'),
        ]
        # Reviews from different users
        admin_user = User.objects.filter(is_superuser=True).first()
        all_users = list(User.objects.all())
        for ridx, (author, rating, text) in enumerate(reviews_data):
            user = all_users[ridx % len(all_users)] if all_users else admin_user
            Review.objects.get_or_create(
                author_name=author,
                defaults={'rating': rating, 'text': text, 'is_approved': True, 'user': user})

        # ── Schedules ─────────────────────────────────────────────────────
        weekdays = [0, 1, 2, 3, 4]
        for doc in doctor_objs[:5]:
            for day in weekdays:
                Schedule.objects.get_or_create(
                    doctor=doc, weekday=day,
                    defaults={'time_from': time(8, 0), 'time_to': time(16, 0)})

        # ── Appointments (>=10) ───────────────────────────────────────────
        statuses = ['planned', 'completed', 'completed', 'completed', 'cancelled']
        appt_objs = []
        base_date = date.today() - timedelta(days=60)
        for i, client in enumerate(client_objs):
            doc = doctor_objs[i % len(doctor_objs)]
            appt_date = base_date + timedelta(days=i * 5)
            appt, created = Appointment.objects.get_or_create(
                client=client, doctor=doc,
                appointment_date=timezone.make_aware(
                    __import__('datetime').datetime.combine(appt_date, time(9 + i % 8, 0))),
                defaults={'status': statuses[i % len(statuses)],
                          'notes': f'Плановый приём пациента {client.last_name}'}
            )
            if created:
                svc = svc_objs[i % len(svc_objs)]
                appt.services.add(svc)
            appt_objs.append(appt)

        # ── Sales ─────────────────────────────────────────────────────────
        promo_list = list(PromoCode.objects.filter(is_active=True))
        for appt in appt_objs:
            if appt.status == 'completed' and not hasattr(appt, 'sale'):
                if not Sale.objects.filter(appointment=appt).exists():
                    total = sum(s.price for s in appt.services.all()) or Decimal('30.00')
                    promo = random.choice(promo_list) if random.random() > 0.5 else None
                    Sale.objects.create(
                        appointment=appt,
                        total_amount=total,
                        promo_code=promo,
                        paid_at=timezone.now() - timedelta(days=random.randint(1, 60))
                    )

        # ── ClientDiagnoses ───────────────────────────────────────────────
        for i, client in enumerate(client_objs[:8]):
            diag = diag_objs[i % len(diag_objs)]
            doc = doctor_objs[i % len(doctor_objs)]
            ClientDiagnosis.objects.get_or_create(
                client=client, diagnosis=diag,
                defaults={'doctor': doc,
                          'date_set': date.today() - timedelta(days=random.randint(30, 365)),
                          'notes': 'Диагноз установлен при осмотре'})

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Superuser:      admin / admin123')
        self.stdout.write('  Doctor example: dr_ivanov / doctor123')
        self.stdout.write('  Client example: client_petrov / client123')
