// ===== PAROL TIZIMI =====
const AUTH_KEY = 'inavatsilya_authenticated';
const VALID_CREDENTIALS = {
    username: 'Inavatsiya2025',
    password: 'Odina1221'
};

// ===== TEST SAVOLLARI (400 TA) =====
const questionsData = [
  {
    question: "Innovatsion ta'lim texnologiyalarining asosiy maqsadi nima?",
    options: [
      "O'quv jarayonini takomillashtirish",
      "O'quvchilarni sinovdan o'tkazish",
      "Ta'lim sohasida yangiliklar yaratish",
      "O'qituvchilarni ishga joylashtirish"
    ],
    correctAnswer: "O'quv jarayonini takomillashtirish"
  },
  {
    question: "Haqiqiy ta'lim texnologiyalarining asosiy afzalliklaridan biri nima?",
    options: [
      "O'quv jarayonining samaradorligini oshirish",
      "Faoliyatni avtomatlashtirish",
      "Faqat testlardan foydalanishga o'rgatish",
      "Ishlash vaqtini kamaytirish"
    ],
    correctAnswer: "O'quv jarayonining samaradorligini oshirish"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarini qo'llashda qanday asosiy metodlardan foydalaniladi?",
    options: [
      "Interaktiv va multimedia metodlari",
      "Vaqtni qisqartirish metodlari",
      "Tekshirish va tahlil metodlari",
      "Yozma va og'zaki metodlar"
    ],
    correctAnswer: "Interaktiv va multimedia metodlari"
  },
  {
    question: "Masofaviy ta'limda asosiy vosita nima?",
    options: [
      "Kompyuterlar va internet",
      "Kitoblar",
      "O'quvchilarni bir joyga to'plash",
      "Mobil telefonlar"
    ],
    correctAnswer: "Kompyuterlar va internet"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarining qayta aloqa tizimi nima?",
    options: [
      "O'quv jarayonining natijalarini tahlil qilish",
      "O'quvchilarning xatolarini belgilash",
      "Baholash tizimi",
      "O'quvchilarni rag'batlantirish usuli"
    ],
    correctAnswer: "O'quv jarayonining natijalarini tahlil qilish"
  },
  {
    question: "Blended learning (aralash ta'lim) nima?",
    options: [
      "Faqat masofaviy ta'lim",
      "An'anaviy ta'lim va masofaviy ta'limning kombinatsiyasi",
      "Faqat amaliy mashg'ulotlar",
      "Faqat nazariy bilimlar"
    ],
    correctAnswer: "An'anaviy ta'lim va masofaviy ta'limning kombinatsiyasi"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarini rivojlantirishda qaysi omil muhim?",
    options: [
      "O'qituvchilarning kasbiy tayyorgarligi",
      "O'quvchilar soni",
      "Maktab binosi kattaligi",
      "O'quv dasturi doimiy o'zgarishi"
    ],
    correctAnswer: "O'qituvchilarning kasbiy tayyorgarligi"
  },
  {
    question: "Ta'lim jarayonida virtual reallik (VR) qanday imkoniyatlar beradi?",
    options: [
      "Faqat yozishni o'rgatish",
      "Amaliy tajribalarni xavfsiz muhitda amalga oshirish",
      "O'quvchilarni uyda qoldirish",
      "Faqat nazariy bilim berish"
    ],
    correctAnswer: "Amaliy tajribalarni xavfsiz muhitda amalga oshirish"
  },
  {
    question: "Innovatsion ta'limda foydalaniladigan eng muhim vositalardan biri?",
    options: [
      "Ovozli diktofonlar",
      "Multimedia proyektorlari va interaktiv doskalar",
      "Qalam va daftar",
      "Faqat kitoblar"
    ],
    correctAnswer: "Multimedia proyektorlari va interaktiv doskalar"
  },
  {
    question: "Gamifikatsiya (o'yinlashtirish) ta'limda nimani nazarda tutadi?",
    options: [
      "O'quv jarayoniga o'yin elementlarini kiritish",
      "Faqat kompyuter o'yinlari o'ynash",
      "O'quvchilarni jazolash",
      "Faqat nazorat qilish"
    ],
    correctAnswer: "O'quv jarayoniga o'yin elementlarini kiritish"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarining asosiy turlari qaysilar?",
    options: [
      "Axborot-kommunikatsiya texnologiyalari (AKT), Blended learning, VR/AR, Gamifikatsiya",
      "Faqat kitob va doska",
      "Faqat yozma va og'zaki darslar",
      "Faqat jismoniy mashg'ulotlar"
    ],
    correctAnswer: "Axborot-kommunikatsiya texnologiyalari (AKT), Blended learning, VR/AR, Gamifikatsiya"
  },
  {
    question: "AKT (Axborot-kommunikatsiya texnologiyalari) nima?",
    options: [
      "Faqat telefonlar",
      "Axborotni yig'ish, qayta ishlash, saqlash va uzatish uchun ishlatiladigan vositalar va usullar",
      "Faqat qog'oz ishlar",
      "Faqat sport anjomlari"
    ],
    correctAnswer: "Axborotni yig'ish, qayta ishlash, saqlash va uzatish uchun ishlatiladigan vositalar va usullar"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarini rivojlantirishdagi asosiy muammo?",
    options: [
      "O'quvchilarning faolsizligi",
      "Texnik infratuzilmaning yetishmasligi va o'qituvchilarni tayyorlashning murakkabligi",
      "O'quv dasturining osonligi",
      "Faqat baholash tizimi"
    ],
    correctAnswer: "Texnik infratuzilmaning yetishmasligi va o'qituvchilarni tayyorlashning murakkabligi"
  },
  {
    question: "Ta'limda o'qituvchining innovatsion roli nima?",
    options: [
      "Faqat ma'ruza o'qish",
      "O'quv jarayonini tashkil etuvchi, yo'naltiruvchi (fasilitator) va maslahatchi",
      "Faqat jazolash",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "O'quv jarayonini tashkil etuvchi, yo'naltiruvchi (fasilitator) va maslahatchi"
  },
  {
    question: "Ta'limda mobil ilovalardan foydalanishning afzalligi?",
    options: [
      "Faqat uyda qolish",
      "O'rganishda erkinlik, moslashuvchanlik va istalgan joyda bilim olish imkoniyati",
      "Faqat darslikni o'qish",
      "Faqat yozma ishlar"
    ],
    correctAnswer: "O'rganishda erkinlik, moslashuvchanlik va istalgan joyda bilim olish imkoniyati"
  },
  {
    question: "Innovatsion ta'limda 'loyihaviy usul' (project method) nima?",
    options: [
      "Faqat yozma ish",
      "O'quvchilarni muammoni mustaqil hal qilishga va amaliy natija olishga yo'naltiradigan metod",
      "Faqat ma'ruza",
      "Faqat test"
    ],
    correctAnswer: "O'quvchilarni muammoni mustaqil hal qilishga va amaliy natija olishga yo'naltiradigan metod"
  },
  {
    question: "Web 2.0 texnologiyalari ta'limda qanday ahamiyatga ega?",
    options: [
      "Faqat ma'lumot olish",
      "O'quvchilar o'rtasida hamkorlik, fikr almashish va kontent yaratish imkoniyati (bloglar, vikilar, ijtimoiy tarmoqlar)",
      "Faqat darslik o'qish",
      "Faqat eshitish"
    ],
    correctAnswer: "O'quvchilar o'rtasida hamkorlik, fikr almashish va kontent yaratish imkoniyati (bloglar, vikilar, ijtimoiy tarmoqlar)"
  },
  {
    question: "AKT yordamida o'quvchilarning mustaqil ishlashini tashkil etishda nimalardan foydalaniladi?",
    options: [
      "Faqat qora doska",
      "Elektron kutubxonalar, onlayn kurslar (MOOC), virtual laboratoriyalar",
      "Faqat darslik",
      "Faqat yozma ish"
    ],
    correctAnswer: "Elektron kutubxonalar, onlayn kurslar (MOOC), virtual laboratoriyalar"
  },
  {
    question: "Ta'lim sifatini oshirishda innovatsion texnologiyalar qanday yordam beradi?",
    options: [
      "Faqat o'qituvchiga yordam berish",
      "Shaxsiylashtirilgan o'quv traektoriyasini yaratish va o'quv materiallarini vizuallashtirish",
      "Faqat vaqtni kamaytirish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "Shaxsiylashtirilgan o'quv traektoriyasini yaratish va o'quv materiallarini vizuallashtirish"
  },
  {
    question: "Innovatsion ta'limda 'Keys-stadi' (vaziyatli tahlil) usuli nima?",
    options: [
      "Faqat ma'ruza",
      "Haqiqiy yoki xayoliy muammoli vaziyatni tahlil qilib, yechim topishga qaratilgan amaliy metod",
      "Faqat test",
      "Faqat yodlash"
    ],
    correctAnswer: "Haqiqiy yoki xayoliy muammoli vaziyatni tahlil qilib, yechim topishga qaratilgan amaliy metod"
  },
  {
    question: "AKT vositalari ta'limda nimani rivojlantiradi?",
    options: [
      "Faqat yozish qobiliyatini",
      "Axborotni izlash, tanqidiy fikrlash, tahlil qilish va kommunikatsiya ko'nikmalarini",
      "Faqat yugurish qobiliyatini",
      "Faqat jismoniy kuchni"
    ],
    correctAnswer: "Axborotni izlash, tanqidiy fikrlash, tahlil qilish va kommunikatsiya ko'nikmalarini"
  },
  {
    question: "Innovatsion texnologiyalarni qo'llashda o'qituvchidan talab qilinadigan asosiy kompetensiya?",
    options: [
      "Faqat ma'ruza qilish",
      "Axborot savodxonligi, media kompetensiya, texnologik va didaktik kompetensiyalar",
      "Faqat sport bilan shug'ullanish",
      "Faqat uyda o'tirish"
    ],
    correctAnswer: "Axborot savodxonligi, media kompetensiya, texnologik va didaktik kompetensiyalar"
  },
  {
    question: "Ta'limda 'Flipped Classroom' (o'girilgan sinf) modeli nimani anglatadi?",
    options: [
      "Faqat uy vazifasi berish",
      "Nazariyani uyda mustaqil o'rganish, sinfda esa amaliyot va muammolarni muhokama qilish",
      "Faqat ma'ruza o'qish",
      "Faqat test ishlash"
    ],
    correctAnswer: "Nazariyani uyda mustaqil o'rganish, sinfda esa amaliyot va muammolarni muhokama qilish"
  },
  {
    question: "AR (Augmented Reality - to'ldirilgan reallik) ta'limda qanday qo'llaniladi?",
    options: [
      "Faqat kompyuter o'yinlari",
      "Real muhitga virtual ob'ektlar, ma'lumotlar va animatsiyalarni qo'shish (masalan, telefon kamerasi orqali)",
      "Faqat yozish",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Real muhitga virtual ob'ektlar, ma'lumotlar va animatsiyalarni qo'shish (masalan, telefon kamerasi orqali)"
  },
  {
    question: "Innovatsion ta'limning pedagogik maqsadi nima?",
    options: [
      "Faqat baho qo'yish",
      "O'quvchilarning kreativlik, mustaqil fikrlash va ijtimoiy ko'nikmalarini rivojlantirish",
      "Faqat darslikni yodlash",
      "Faqat nazorat"
    ],
    correctAnswer: "O'quvchilarning kreativlik, mustaqil fikrlash va ijtimoiy ko'nikmalarini rivojlantirish"
  },
  {
    question: "Elektron darsliklarning afzalligi nima?",
    options: [
      "Faqat qimmatligi",
      "Interaktivlik, yangilanish imkoniyati, multimedia materiallari bilan boyitilganligi",
      "Faqat og'irligi",
      "Faqat yozma matn"
    ],
    correctAnswer: "Interaktivlik, yangilanish imkoniyati, multimedia materiallari bilan boyitilganligi"
  },
  {
    question: "Masofaviy ta'limning asosiy talabi?",
    options: [
      "Faqat sinfda o'tirish",
      "O'quvchidan yuqori darajadagi o'z-o'zini boshqarish va motivatsiya talab etilishi",
      "Faqat yozma imtihon",
      "Faqat ma'ruza"
    ],
    correctAnswer: "O'quvchidan yuqori darajadagi o'z-o'zini boshqarish va motivatsiya talab etilishi"
  },
  {
    question: "Ta'limdagi innovatsion yondashuv nimani o'zgartiradi?",
    options: [
      "Faqat o'qituvchini",
      "O'qitish metodlari, o'quv materiallari mazmuni va ta'lim muhitini",
      "Faqat maktab binosini",
      "Faqat o'quvchilar sonini"
    ],
    correctAnswer: "O'qitish metodlari, o'quv materiallari mazmuni va ta'lim muhitini"
  },
  {
    question: "Innovatsion ta'limda simulyatsiya (o'xshatish) nima uchun kerak?",
    options: [
      "Faqat dam olish",
      "Murakkab jarayonlarni, operatsiyalarni va amaliy ko'nikmalarni xavfsiz o'rganish uchun",
      "Faqat yozish",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Murakkab jarayonlarni, operatsiyalarni va amaliy ko'nikmalarni xavfsiz o'rganish uchun"
  },
  {
    question: "Ta'limda 'Mantiqiy yondashuv' deganda nimani tushunasiz?",
    options: [
      "Faqat yodlash",
      "Axborotni mantiqiy, tizimli ravishda tahlil qilish va xulosa chiqarishga o'rgatish",
      "Faqat o'ynash",
      "Faqat harakat"
    ],
    correctAnswer: "Axborotni mantiqiy, tizimli ravishda tahlil qilish va xulosa chiqarishga o'rgatish"
  },
  {
    question: "O'qitish jarayonida 'Brainstorming' (aqliy hujum) usuli nimani rivojlantiradi?",
    options: [
      "Faqat jismoniy kuchni",
      "Kreativlikni, muammo yechish qobiliyatini va guruhda ishlashni",
      "Faqat yozishni",
      "Faqat yodlashni"
    ],
    correctAnswer: "Kreativlikni, muammo yechish qobiliyatini va guruhda ishlashni"
  },
  {
    question: "AKT yordamida **Differensiallashtirilgan yondashuv** qanday amalga oshiriladi?",
    options: [
      "Faqat bir xil dars berish",
      "Har bir o'quvchiga uning bilim darajasi va ehtiyojiga mos materiallar va topshiriqlar berish",
      "Faqat test ishlash",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Har bir o'quvchiga uning bilim darajasi va ehtiyojiga mos materiallar va topshiriqlar berish"
  },
  {
    question: "O'quv jarayonida **Kollaborativ filtratsiya** nima?",
    options: [
      "Faqat o'qituvchi tanlovi",
      "O'quvchilarning avvalgi tanlovlari asosida ularga mos keladigan yangi materiallarni taklif qilish",
      "Faqat tasodifiy tanlash",
      "Faqat kitob o'qish"
    ],
    correctAnswer: "O'quvchilarning avvalgi tanlovlari asosida ularga mos keladigan yangi materiallarni taklif qilish"
  },
  {
    question: "Zamonaviy ta'limdagi **Intellektual Agentlar (AI)** qanday yordam beradi?",
    options: [
      "Faqat jazolash",
      "O'quvchilarning savollariga javob berish, avtomatik baholash va individual yordam berish",
      "Faqat ma'ruza",
      "Faqat yozish"
    ],
    correctAnswer: "O'quvchilarning savollariga javob berish, avtomatik baholash va individual yordam berish"
  },
  {
    question: "**Kritik fikrlash (Critical Thinking)** ta'limda nima uchun muhim?",
    options: [
      "Faqat yodlash uchun",
      "Axborotni baholash, xulosalarni mantiqan asoslash va muammolarni samarali yechish qobiliyatini shakllantirish",
      "Faqat eshitish uchun",
      "Faqat ko'rish uchun"
    ],
    correctAnswer: "Axborotni baholash, xulosalarni mantiqan asoslash va muammolarni samarali yechish qobiliyatini shakllantirish"
  },
  {
    question: "Innovatsion ta'limning asosiy **vazifasi** nima?",
    options: [
      "Faqat darslik yaratish",
      "O'quvchilarning shaxsiy va professional rivojlanishi uchun zarur bo'lgan kompetensiyalarni shakllantirish",
      "Faqat vaqtni tejash",
      "Faqat test ishlash"
    ],
    correctAnswer: "O'quvchilarning shaxsiy va professional rivojlanishi uchun zarur bo'lgan kompetensiyalarni shakllantirish"
  },
  {
    question: "Ta'limda **Portfolio usuli** qanday baholash turi?",
    options: [
      "Faqat yozma imtihon",
      "O'quvchining uzoq muddat davomidagi ish namunalari, yutuqlari va o'sishini aks ettiruvchi to'plam orqali baholash",
      "Faqat test",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "O'quvchining uzoq muddat davomidagi ish namunalari, yutuqlari va o'sishini aks ettiruvchi to'plam orqali baholash"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarida **Axborot xavfsizligi** masalasi nima uchun muhim?",
    options: [
      "Faqat kompyuterni himoyalash",
      "O'quvchilarning shaxsiy ma'lumotlari, o'quv materiallari va tizimga ruxsatsiz kirishdan himoyalash",
      "Faqat elektr energiyasini tejash",
      "Faqat yozish"
    ],
    correctAnswer: "O'quvchilarning shaxsiy ma'lumotlari, o'quv materiallari va tizimga ruxsatsiz kirishdan himoyalash"
  },
  {
    question: "**Kollaborativ (hamkorlikdagi) o'rganish** nimani anglatadi?",
    options: [
      "Faqat individual ish",
      "O'quvchilarning kichik guruhlarda birgalikda ishlash, fikr almashish va umumiy maqsadga erishish",
      "Faqat o'qituvchi bilan ishlash",
      "Faqat jazolash"
    ],
    correctAnswer: "O'quvchilarning kichik guruhlarda birgalikda ishlash, fikr almashish va umumiy maqsadga erishish"
  },
  {
    question: "Ta'limda **Onlayn forumlar va chatlar**ning asosiy funksiyasi nima?",
    options: [
      "Faqat dam olish",
      "O'quv materiallarini muhokama qilish, savollar berish va doimiy qayta aloqani ta'minlash",
      "Faqat rasm chizish",
      "Faqat yozish"
    ],
    correctAnswer: "O'quv materiallarini muhokama qilish, savollar berish va doimiy qayta aloqani ta'minlash"
  },
  {
    question: "Ta'limda **Modellashtirish usuli** nima?",
    options: [
      "Faqat darslik o'qish",
      "O'rganilayotgan obyekt yoki jarayonning soddalashtirilgan modelini yaratish va uni tadqiq qilish",
      "Faqat ma'ruza",
      "Faqat test"
    ],
    correctAnswer: "O'rganilayotgan obyekt yoki jarayonning soddalashtirilgan modelini yaratish va uni tadqiq qilish"
  },
  {
    question: "Innovatsion texnologiyalarning **didaktik** funksiyasi nima?",
    options: [
      "Faqat baho qo'yish",
      "O'quv materiallarini taqdim etish, bilim va ko'nikmalarni shakllantirish, nazorat qilish",
      "Faqat tarbiya berish",
      "Faqat dam olish"
    ],
    correctAnswer: "O'quv materiallarini taqdim etish, bilim va ko'nikmalarni shakllantirish, nazorat qilish"
  },
  {
    question: "Innovatsion ta'limda **O'z-o'zini baholash (Self-assessment)** qanday o'rin tutadi?",
    options: [
      "Faqat jazolash",
      "O'quvchining o'z o'rganish jarayoni va natijalarini mustaqil tahlil qilib, xulosalar chiqarishi",
      "Faqat o'qituvchini baholash",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "O'quvchining o'z o'rganish jarayoni va natijalarini mustaqil tahlil qilib, xulosalar chiqarishi"
  },
  {
    question: "**Interfaol usullar**ning asosiy afzalligi?",
    options: [
      "Faqat yodlash",
      "O'quvchilarni faol ishtirok etishga, muloqotga va muammoli vaziyatlarni hal qilishga undash",
      "Faqat eshitish",
      "Faqat ko'rish"
    ],
    correctAnswer: "O'quvchilarni faol ishtirok etishga, muloqotga va muammoli vaziyatlarni hal qilishga undash"
  },
  {
    question: "Ta'limda **Mobil texnologiyalar**dan foydalanishning **salbiy tomoni** nima?",
    options: [
      "Faqat qulayligi",
      "Diqqatni chalg'itish, texnik nosozliklar va axborot xavfsizligi xavfi",
      "Faqat arzonligi",
      "Faqat tezligi"
    ],
    correctAnswer: "Diqqatni chalg'itish, texnik nosozliklar va axborot xavfsizligi xavfi"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarini joriy etishda **asosiy qadam** nima?",
    options: [
      "Faqat bino qurish",
      "O'qituvchilarni ushbu texnologiyalardan foydalanishga o'qitish va ularning kasbiy mahoratini oshirish",
      "Faqat darslik sotib olish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "O'qituvchilarni ushbu texnologiyalardan foydalanishga o'qitish va ularning kasbiy mahoratini oshirish"
  },
  {
    question: "**Psixika** deganda nimani tushunasiz?",
    options: [
      "Faqat tana harakatlari",
      "Miyaning olamni aks ettiruvchi, borliqqa nisbatan faol munosabatini ifodalovchi xususiyati",
      "Faqat xotira",
      "Faqat tashqi muhit"
    ],
    correctAnswer: "Miyaning olamni aks ettiruvchi, borliqqa nisbatan faol munosabatini ifodalovchi xususiyati"
  },
  {
    question: "Psixologiya fanining **asosiy predmeti** nima?",
    options: [
      "Faqat insonning tanasi",
      "Inson va hayvonlarning psixikasi, psixik faoliyatining qonuniyatlari",
      "Faqat darsliklar",
      "Faqat tabiiy hodisalar"
    ],
    correctAnswer: "Inson va hayvonlarning psixikasi, psixik faoliyatining qonuniyatlari"
  },
  {
    question: "Psixik hodisalar tarkibiga kiruvchi **shaxsning individual ruhiy xususiyatlari** qaysi qatorda koërsatilgan?",
    options: [
      "Sezgi, idrok, xotira, tafakkur",
      "Temperament, xarakter, qobiliyat",
      "Hissiyot, iroda",
      "Diqqat, nutq, faoliyat"
    ],
    correctAnswer: "Temperament, xarakter, qobiliyat"
  },
  {
    question: "**Diqqatning kontsentratsiyasi** nima?",
    options: [
      "Faqat joyni o'zgartirish",
      "Insonning oëz diqqatini maílum obyektga uzoq vaqt davomida barqaror qaratib tura olishi",
      "Faqat eslab qolish tezligi",
      "Faqat yozish"
    ],
    correctAnswer: "Insonning oëz diqqatini maílum obyektga uzoq vaqt davomida barqaror qaratib tura olishi"
  },
  {
    question: "**Sezgi** qanday psixik jarayon?",
    options: [
      "Faqat fikrlash",
      "Tashqi va ichki muhitdagi alohida xususiyatlarning (rang, hid, harorat) bevosita miyada aks etishi",
      "Faqat xayol",
      "Faqat harakat"
    ],
    correctAnswer: "Tashqi va ichki muhitdagi alohida xususiyatlarning (rang, hid, harorat) bevosita miyada aks etishi"
  },
  {
    question: "**Idrok** (Vospriyatiye) nima?",
    options: [
      "Faqat bir xususiyatni aks ettirish",
      "Obíektlarni (narsalarni) butun holda, uning barcha xususiyatlari majmuida aks ettirish",
      "Faqat yozish",
      "Faqat xotira"
    ],
    correctAnswer: "Obíektlarni (narsalarni) butun holda, uning barcha xususiyatlari majmuida aks ettirish"
  },
  {
    question: "**Tafakkur**ning asosiy funksiyasi?",
    options: [
      "Faqat sezish",
      "Borliqning shaxsga bevosita berilmagan tomonlarini umumlashtirish va bilvosita (tushuncha, mulohaza, xulosa orqali) aks ettirish",
      "Faqat ko'rish",
      "Faqat eslab qolish"
    ],
    correctAnswer: "Borliqning shaxsga bevosita berilmagan tomonlarini umumlashtirish va bilvosita (tushuncha, mulohaza, xulosa orqali) aks ettirish"
  },
  {
    question: "**Xotira**ning asosiy jarayonlari qaysilar?",
    options: [
      "Faqat gapirish",
      "Eslab qolish (saqlash), esda saqlash, esga tushirish (tanib olish va qayta tiklash)",
      "Faqat harakat",
      "Faqat ko'rish"
    ],
    correctAnswer: "Eslab qolish (saqlash), esda saqlash, esga tushirish (tanib olish va qayta tiklash)"
  },
  {
    question: "**Xayol** (Fantaziya) qanday psixik jarayon?",
    options: [
      "Faqat yodlash",
      "Yangi obrazlar, tasavvurlar va g'oyalarni yaratishga qaratilgan aqliy jarayon",
      "Faqat jazolash",
      "Faqat tana harakati"
    ],
    correctAnswer: "Yangi obrazlar, tasavvurlar va g'oyalarni yaratishga qaratilgan aqliy jarayon"
  },
  {
    question: "Tafakkur turlari qaysi qatorda to'g'ri ko'rsatilgan?",
    options: [
      "Faqat ko'rgazmali",
      "Ko'rgazmali-harakatli, ko'rgazmali-obrazli, so'z-mantiqiy",
      "Faqat eslab qolish",
      "Faqat sezish"
    ],
    correctAnswer: "Ko'rgazmali-harakatli, ko'rgazmali-obrazli, so'z-mantiqiy"
  },
  {
    question: "**Temperament** nima?",
    options: [
      "Faqat bilim",
      "Shaxsning psixik faoliyatining dinamik tomonini (tezligi, kuchi, ritmi) belgilovchi tug'ma xususiyati",
      "Faqat xarakter",
      "Faqat qobiliyat"
    ],
    correctAnswer: "Shaxsning psixik faoliyatining dinamik tomonini (tezligi, kuchi, ritmi) belgilovchi tug'ma xususiyati"
  },
  {
    question: "Galen bo'yicha **temperamentning asosiy turlari** qaysilar?",
    options: [
      "Faqat tez va sekin",
      "Xolerik, Sangvinik, Flegmatik, Melanxolik",
      "Faqat quvnoq va xafa",
      "Faqat kuchli va kuchsiz"
    ],
    correctAnswer: "Xolerik, Sangvinik, Flegmatik, Melanxolik"
  },
  {
    question: "**Xarakter** nima?",
    options: [
      "Faqat tug'ma",
      "Shaxsning ijtimoiy munosabatlarda shakllanadigan, uning xatti-harakatlarida namoyon bo'ladigan barqaror individual xususiyatlari majmui",
      "Faqat eslab qolish",
      "Faqat sezish"
    ],
    correctAnswer: "Shaxsning ijtimoiy munosabatlarda shakllanadigan, uning xatti-harakatlarida namoyon bo'ladigan barqaror individual xususiyatlari majmui"
  },
  {
    question: "**Qobiliyat** nima?",
    options: [
      "Faqat harakat",
      "Muayyan faoliyatni muvaffaqiyatli bajarish uchun zarur bo'lgan individual-psixologik xususiyatlar",
      "Faqat xarakter",
      "Faqat temperament"
    ],
    correctAnswer: "Muayyan faoliyatni muvaffaqiyatli bajarish uchun zarur bo'lgan individual-psixologik xususiyatlar"
  },
  {
    question: "Qobiliyatning eng yuqori darajasi nima?",
    options: [
      "Ko'nikma",
      "Iste'dod (Talant) va zakovat (Aql-idrok)",
      "Malaka",
      "Xotira"
    ],
    correctAnswer: "Iste'dod (Talant) va zakovat (Aql-idrok)"
  },
  {
    question: "Psixik hodisalar tarkibiga kiruvchi **psixik holatlar** qaysilar?",
    options: [
      "Temperament, xarakter",
      "Eslab qolish, unutish",
      "Hissiyot, stress, kayfiyat, ishtiyoq (affekt)",
      "Nutq, faoliyat"
    ],
    correctAnswer: "Hissiyot, stress, kayfiyat, ishtiyoq (affekt)"
  },
  {
    question: "**Hissiyot** (Emotsiya) nima?",
    options: [
      "Faqat fikrlash",
      "Borliq hodisalariga nisbatan shaxsning subyektiv (ichki) baholovchi munosabatini ifodalovchi psixik jarayon",
      "Faqat yurish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Borliq hodisalariga nisbatan shaxsning subyektiv (ichki) baholovchi munosabatini ifodalovchi psixik jarayon"
  },
  {
    question: "**Affekt** (Ishtiyoq) qanday hissiy holat?",
    options: [
      "Uzoq davom etadigan, sust kayfiyat",
      "Qisqa muddatli, kuchli, shiddatli va keskin bo'ladigan hissiy portlash holati",
      "Faqat xotira",
      "Faqat fikr"
    ],
    correctAnswer: "Qisqa muddatli, kuchli, shiddatli va keskin bo'ladigan hissiy portlash holati"
  },
  {
    question: "**Iroda** (Volya) nima?",
    options: [
      "Faqat orzu",
      "Shaxsning oëz xatti-harakatlari, fikrlari va hissiyotlarini ongli ravishda boshqarish qobiliyati",
      "Faqat tana kuchi",
      "Faqat temperament"
    ],
    correctAnswer: "Shaxsning oëz xatti-harakatlari, fikrlari va hissiyotlarini ongli ravishda boshqarish qobiliyati"
  },
  {
    question: "Irodaviy harakatning asosiy bosqichlari?",
    options: [
      "Faqat harakat",
      "Maqsadni belgilash, harakat sabablarini kurashishi, qaror qabul qilish, uni amalga oshirish",
      "Faqat gapirish",
      "Faqat o'ylash"
    ],
    correctAnswer: "Maqsadni belgilash, harakat sabablarini kurashishi, qaror qabul qilish, uni amalga oshirish"
  },
  {
    question: "O'ziga bo'lgan **munosabatni ifodalovchi sifatlar** qaysi qatorda koërsatilgan?",
    options: [
      "Yaxshilik, mehribonlik",
      "Gëururlilik, shuhratparastlik, magërurlik, oëzini ulugëlash, kamtarlik",
      "Mehnatsevarlik, dangasalik",
      "Tozalik yoki ifloslik"
    ],
    correctAnswer: "Gëururlilik, shuhratparastlik, magërurlik, oëzini ulugëlash, kamtarlik"
  },
  {
    question: "**Interes** (Qiziqish) qanday psixik hodisa?",
    options: [
      "Faqat zerikish",
      "Shaxsning ma'lum faoliyatga, bilim olishga yo'nalganligi va uning ahamiyatini anglash",
      "Faqat tashqi muhit",
      "Faqat ovqatlanish"
    ],
    correctAnswer: "Shaxsning ma'lum faoliyatga, bilim olishga yo'nalganligi va uning ahamiyatini anglash"
  },
  {
    question: "**Ehtiyoj** (Nujda) nima?",
    options: [
      "Faqat xohish",
      "Shaxsning yashashi va rivojlanishi uchun zarur bo'lgan narsalar yetishmasligini anglash holati, faoliyatning manbai",
      "Faqat bilim",
      "Faqat temperament"
    ],
    correctAnswer: "Shaxsning yashashi va rivojlanishi uchun zarur bo'lgan narsalar yetishmasligini anglash holati, faoliyatning manbai"
  },
  {
    question: "A. Maslou bo'yicha ehtiyojlar piramidasining **eng quyi pog'onasi** nima?",
    options: [
      "Boshqalarni hurmat qilish ehtiyoji",
      "Fiziologik ehtiyojlar (ovqat, uyqu, nafas olish)",
      "Xavfsizlik ehtiyoji",
      "O'zini namoyon qilish ehtiyoji"
    ],
    correctAnswer: "Fiziologik ehtiyojlar (ovqat, uyqu, nafas olish)"
  },
  {
    question: "**Shaxs** (Lichnost) nima?",
    options: [
      "Faqat tug'ma xususiyatlar",
      "Ijtimoiy munosabatlar jarayonida shakllangan, o'ziga xos ongga ega bo'lgan subyekt",
      "Faqat tana",
      "Faqat miya"
    ],
    correctAnswer: "Ijtimoiy munosabatlar jarayonida shakllangan, o'ziga xos ongga ega bo'lgan subyekt"
  },
  {
    question: "**Individ** (Individual) tushunchasi nimani anglatadi?",
    options: [
      "Faqat ijtimoiy xususiyatlar",
      "Inson turining alohida vakili, uning tug'ma, biologik xususiyatlari majmui",
      "Faqat xarakter",
      "Faqat bilim"
    ],
    correctAnswer: "Inson turining alohida vakili, uning tug'ma, biologik xususiyatlari majmui"
  },
  {
    question: "**Individual yondashuv** (Psixologiyada) nimani anglatadi?",
    options: [
      "Faqat guruh bilan ishlash",
      "Ta'lim-tarbiya jarayonida har bir o'quvchining individual-psixologik xususiyatlarini (temperament, xarakter, qobiliyat) hisobga olish",
      "Faqat bir xil dars berish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "Ta'lim-tarbiya jarayonida har bir o'quvchining individual-psixologik xususiyatlarini (temperament, xarakter, qobiliyat) hisobga olish"
  },
  {
    question: "**Intellekt** (Aql-idrok) nima?",
    options: [
      "Faqat xotira",
      "Yangi sharoitga moslasha olish, bilim olish, muammolarni yechish va mavhum fikrlash qobiliyati",
      "Faqat jismoniy kuch",
      "Faqat temperament"
    ],
    correctAnswer: "Yangi sharoitga moslasha olish, bilim olish, muammolarni yechish va mavhum fikrlash qobiliyati"
  },
  {
    question: "Psixologiyada **faoliyat** nima?",
    options: [
      "Faqat yurish",
      "Shaxsning ehtiyojlarini qondirishga, maqsadga erishishga qaratilgan harakatlari majmui",
      "Faqat yozish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Shaxsning ehtiyojlarini qondirishga, maqsadga erishishga qaratilgan harakatlari majmui"
  },
  {
    question: "Faoliyatning asosiy turlari qaysilar?",
    options: [
      "Faqat o'ynash",
      "O'yin, o'qish (o'rganish), mehnat",
      "Faqat yozish, gapirish",
      "Faqat ko'rish, eshitish"
    ],
    correctAnswer: "O'yin, o'qish (o'rganish), mehnat"
  },
  {
    question: "Shaxsning **motivatsiyasi** nima?",
    options: [
      "Faqat qoidalar",
      "Shaxsni faoliyatga undaydigan, uning maqsad va ehtiyojlari bilan bog'liq bo'lgan ichki kuchlar tizimi",
      "Faqat temperament",
      "Faqat malaka"
    ],
    correctAnswer: "Shaxsni faoliyatga undaydigan, uning maqsad va ehtiyojlari bilan bog'liq bo'lgan ichki kuchlar tizimi"
  },
  {
    question: "**Krizis** (Inqiroz) yosh davrlari psixologiyasida nimani anglatadi?",
    options: [
      "Faqat kasallik",
      "Bolaning psixik rivojlanishida yangi sifat bosqichiga o'tish bilan bog'liq bo'lgan qisqa, keskin o'zgarishlar davri",
      "Faqat dam olish",
      "Faqat o'ynash"
    ],
    correctAnswer: "Bolaning psixik rivojlanishida yangi sifat bosqichiga o'tish bilan bog'liq bo'lgan qisqa, keskin o'zgarishlar davri"
  },
  {
    question: "**O'smirlik davri** (11-15 yosh) psixologik xususiyatlari?",
    options: [
      "Faqat o'yin",
      "Tana o'zgarishlari, o'zlikni anglashning kuchayishi, yetakchilikka intilish, mustaqillikka ehtiyoj",
      "Faqat ota-onaga bo'ysunish",
      "Faqat maktabga borish"
    ],
    correctAnswer: "Tana o'zgarishlari, o'zlikni anglashning kuchayishi, yetakchilikka intilish, mustaqillikka ehtiyoj"
  },
  {
    question: "Bolaning rivojlanishida **o'yin faoliyati**ning asosiy o'rni nima?",
    options: [
      "Faqat vaqt o'tkazish",
      "Ijtimoiy munosabatlarni, muloqotni, irodani va rolli xatti-harakatlarni o'rganish",
      "Faqat ovqatlanish",
      "Faqat yozish"
    ],
    correctAnswer: "Ijtimoiy munosabatlarni, muloqotni, irodani va rolli xatti-harakatlarni o'rganish"
  },
  {
    question: "**Kommunikatsiya** (Muloqot) nima?",
    options: [
      "Faqat fikrlash",
      "Odamlar o'rtasida axborot, tajriba, bilim va hissiyotlarni almashish jarayoni",
      "Faqat yurish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Odamlar o'rtasida axborot, tajriba, bilim va hissiyotlarni almashish jarayoni"
  },
  {
    question: "Muloqotning **verbal** (og'zaki) vositalariga nimalar kiradi?",
    options: [
      "Mimika, jestlar",
      "Nutq, so'z, ovoz ohangi",
      "Kiyim, soch turmagi",
      "Yurish usuli"
    ],
    correctAnswer: "Nutq, so'z, ovoz ohangi"
  },
  {
    question: "Muloqotning **noverbal** (og'zaki bo'lmagan) vositalariga nimalar kiradi?",
    options: [
      "So'zlar, jumlalar",
      "Mimika, jestlar, pantomimika, intonatsiya, nigoh",
      "Ma'ruza",
      "Kitoblar"
    ],
    correctAnswer: "Mimika, jestlar, pantomimika, intonatsiya, nigoh"
  },
  {
    question: "**Stress** qanday psixik holat?",
    options: [
      "Faqat dam olish",
      "Organizmning juda kuchli ta'sirga (xavf, xursandlik, jismoniy zo'riqish) javoban beradigan umumiy javobi (ruhiy va fiziologik keskinlik)",
      "Faqat o'ynash",
      "Faqat uxlash"
    ],
    correctAnswer: "Organizmning juda kuchli ta'sirga (xavf, xursandlik, jismoniy zo'riqish) javoban beradigan umumiy javobi (ruhiy va fiziologik keskinlik)"
  },
  {
    question: "**Konflikt** (Ziddiyat) nima?",
    options: [
      "Faqat do'stlik",
      "Odamlar, guruhlar yoki ichki shaxsiy motivlar o'rtasidagi qarama-qarshi maqsadlar, manfaatlar yoki pozitsiyalar to'qnashuvi",
      "Faqat hamkorlik",
      "Faqat yordam"
    ],
    correctAnswer: "Odamlar, guruhlar yoki ichki shaxsiy motivlar o'rtasidagi qarama-qarshi maqsadlar, manfaatlar yoki pozitsiyalar to'qnashuvi"
  },
  {
    question: "Psixologiyada **'Bilimlar (Kognitiv) jarayonlar'** nimalar?",
    options: [
      "Faqat hissiyot",
      "Sezgi, idrok, xotira, tafakkur, xayol va diqqat",
      "Faqat xarakter",
      "Faqat iroda"
    ],
    correctAnswer: "Sezgi, idrok, xotira, tafakkur, xayol va diqqat"
  },
  {
    question: "**Eidetik xotira** nima?",
    options: [
      "Faqat ovozli xotira",
      "Ob'ektni go'yo uni hali ham ko'rayotgandek, juda aniq va to'liq eslab qolish qobiliyati (fotografik xotira)",
      "Faqat harakat xotirasi",
      "Faqat hissiyot xotirasi"
    ],
    correctAnswer: "Ob'ektni go'yo uni hali ham ko'rayotgandek, juda aniq va to'liq eslab qolish qobiliyati (fotografik xotira)"
  },
  {
    question: "**Analiz** (Tahlil) va **Sintez** (Tafakkurda) nima?",
    options: [
      "Faqat bir jarayon",
      "Analiz - butunni qismlarga ajratish, Sintez - qismlardan butunni yaratish",
      "Faqat eslab qolish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Analiz - butunni qismlarga ajratish, Sintez - qismlardan butunni yaratish"
  },
  {
    question: "**Kreativlik** (Ijodkorlik) nima?",
    options: [
      "Faqat qoidalar bo'yicha ishlash",
      "Yangi va noyob g'oyalar, yechimlar yoki mahsulotlar yaratish qobiliyati",
      "Faqat eslab qolish",
      "Faqat jazolash"
    ],
    correctAnswer: "Yangi va noyob g'oyalar, yechimlar yoki mahsulotlar yaratish qobiliyati"
  },
  {
    question: "**Mijozlarga yo'naltirilgan terapiya** (K. Rodjers) nimani anglatadi?",
    options: [
      "Faqat maslahat berish",
      "Terapistning mijozni qabul qilishi, unga hamdardlik (empatiya) bildirish va uni qo'llab-quvvatlash",
      "Faqat jazolash",
      "Faqat buyruq berish"
    ],
    correctAnswer: "Terapistning mijozni qabul qilishi, unga hamdardlik (empatiya) bildirish va uni qo'llab-quvvatlash"
  },
  {
    question: "A. Maslou bo'yicha ehtiyojlar piramidasining **eng yuqori pog'onasi** nima?",
    options: [
      "Fiziologik ehtiyojlar",
      "Xavfsizlik ehtiyoji",
      "O'zini namoyon qilish (aktualizatsiya) ehtiyoji",
      "Muloqot ehtiyoji"
    ],
    correctAnswer: "O'zini namoyon qilish (aktualizatsiya) ehtiyoji"
  },
  {
    question: "**Neyropsixologiya** nima?",
    options: [
      "Faqat hayvonlar psixologiyasi",
      "Miya tuzilishi va uning alohida qismlari bilan psixik jarayonlar o'rtasidagi bog'liqlikni o'rganadigan fan",
      "Faqat ijtimoiy psixologiya",
      "Faqat kasb psixologiyasi"
    ],
    correctAnswer: "Miya tuzilishi va uning alohida qismlari bilan psixik jarayonlar o'rtasidagi bog'liqlikni o'rganadigan fan"
  },
  {
    question: "**Persepsiya** tushunchasi psixologiyada nimani bildiradi?",
    options: [
      "Sezgi",
      "Idrok",
      "Xotira",
      "Diqqat"
    ],
    correctAnswer: "Idrok"
  },
  {
    question: "**Flegmatik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Haddan tashqari shoshqaloqlik va beqarorlik",
      "Sokin, sust, hissiyotlarni kam namoyon etadigan, sekin, ammo barqaror",
      "Haddan tashqari optimist, serharakat",
      "Haddan tashqari xafa, tushkun"
    ],
    correctAnswer: "Sokin, sust, hissiyotlarni kam namoyon etadigan, sekin, ammo barqaror"
  },
  {
    question: "**Melanxolik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Serharakat, doimo o'zgaruvchan",
      "Juda ta'sirchan, tez charchaydigan, yengil tushkunlikka tushuvchi, sust, o'ziga ishonchsiz",
      "Kuchli, tezkor, hissiyotlarga beriluvchan",
      "Sokin, harakatsiz, deyarli hissiyotsiz"
    ],
    correctAnswer: "Juda ta'sirchan, tez charchaydigan, yengil tushkunlikka tushuvchi, sust, o'ziga ishonchsiz"
  },
  {
    question: "**Holerik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Sokin, bosiq",
      "Kuchli, tezkor, muvozanatsiz, tezda jahli chiqadigan, hissiyotlarga beriluvchan",
      "Serharakat, quvnoq, barqaror",
      "Sust, xafa"
    ],
    correctAnswer: "Kuchli, tezkor, muvozanatsiz, tezda jahli chiqadigan, hissiyotlarga beriluvchan"
  },
  {
    question: "**Sangvinik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Sokin, bosiq, sust",
      "Serharakat, quvnoq, optimist, tez moslashuvchan, hissiyotlari tez o'zgaruvchan",
      "Muvozanatsiz, jahlga tez beriluvchan",
      "Juda ta'sirchan, o'ziga ishonchsiz"
    ],
    correctAnswer: "Serharakat, quvnoq, optimist, tez moslashuvchan, hissiyotlari tez o'zgaruvchan"
  },
  {
    question: "**Appersepsiya** nima?",
    options: [
      "Faqat eslab qolish",
      "Idrokning shaxsning avvalgi tajribasi, bilimi va qiziqishlariga bog'liqligi",
      "Faqat sezish",
      "Faqat xayol"
    ],
    correctAnswer: "Idrokning shaxsning avvalgi tajribasi, bilimi va qiziqishlariga bog'liqligi"
  },
  {
    question: "**Qobiliyatning rivojlanish darajalari** qaysilar?",
    options: [
      "Bilim, ko'nikma",
      "Iste'dod (Talant), Zakovat (Aql-idrok), Geniallik",
      "Malaka, harakat",
      "Diqqat, xotira"
    ],
    correctAnswer: "Iste'dod (Talant), Zakovat (Aql-idrok), Geniallik"
  },
  {
    question: "**Muloqotning perseptiv tomoni** nima?",
    options: [
      "Faqat axborot almashish",
      "Suhbatdoshni (sherikni) idrok etish, uni tushunish va baholash jarayoni",
      "Faqat ta'sir o'tkazish",
      "Faqat so'zlashish"
    ],
    correctAnswer: "Suhbatdoshni (sherikni) idrok etish, uni tushunish va baholash jarayoni"
  },
  {
    question: "**Empatiya** (Psixologiyada) nima?",
    options: [
      "Faqat baholash",
      "Boshqa odamning hissiyotlarini, holatini ichki tomondan tushuna olish va hamdardlik bildirish qobiliyati",
      "Faqat jazolash",
      "Faqat o'ylash"
    ],
    correctAnswer: "Boshqa odamning hissiyotlarini, holatini ichki tomondan tushuna olish va hamdardlik bildirish qobiliyati"
  },
  {
    question: "**Refleksiya** (Psixologiyada) nima?",
    options: [
      "Faqat tashqariga qarash",
      "Shaxsning oëz ichki ruhiy holati, fikrlari, xatti-harakatlari va o'zgarishlarini o'zi tahlil qilishi",
      "Faqat yugurish",
      "Faqat tinglash"
    ],
    correctAnswer: "Shaxsning oëz ichki ruhiy holati, fikrlari, xatti-harakatlari va o'zgarishlarini o'zi tahlil qilishi"
  },
  {
    question: "**Diqqatning barqarorligi** nima?",
    options: [
      "Faqat tez o'tish",
      "Diqqatning ma'lum obyektdan chalg'imasdan, uzoq vaqt davomida saqlana olish qobiliyati",
      "Faqat tez charchash",
      "Faqat bo'linish"
    ],
    correctAnswer: "Diqqatning ma'lum obyektdan chalg'imasdan, uzoq vaqt davomida saqlana olish qobiliyati"
  },
  {
    question: "**O'qish faoliyati** (Psixologiyada) qanday faoliyat turi?",
    options: [
      "Faqat o'yin",
      "Nazariy bilimlar, ko'nikmalar va malakalarni o'zlashtirishga qaratilgan faoliyat",
      "Faqat mehnat",
      "Faqat dam olish"
    ],
    correctAnswer: "Nazariy bilimlar, ko'nikmalar va malakalarni o'zlashtirishga qaratilgan faoliyat"
  },
  {
    question: "Tafakkur jarayonida **generallashuv** (umumlashtirish) nima?",
    options: [
      "Faqat ajratish",
      "Ob'ektlar va hodisalarning muhim va umumiy xususiyatlarini ajratib olish va ularni tushuncha ostida birlashtirish",
      "Faqat taqqoslash",
      "Faqat analiz"
    ],
    correctAnswer: "Ob'ektlar va hodisalarning muhim va umumiy xususiyatlarini ajratib olish va ularni tushuncha ostida birlashtirish"
  },
  {
    question: "**Vizual xotira** nima?",
    options: [
      "Faqat eshitish orqali eslab qolish",
      "Ko'rish orqali idrok qilingan obrazlar va ma'lumotlarni eslab qolish va qayta tiklash",
      "Faqat harakat orqali eslab qolish",
      "Faqat hissiyot orqali eslab qolish"
    ],
    correctAnswer: "Ko'rish orqali idrok qilingan obrazlar va ma'lumotlarni eslab qolish va qayta tiklash"
  },
  {
    question: "**Ijtimoiy idrok** (Sotsialnaya persepsiya) nima?",
    options: [
      "Faqat narsalarni idrok etish",
      "Odamlarning bir-birini, o'zini, ijtimoiy ob'ektlar va guruhlarni idrok etish, tushunish va baholash jarayoni",
      "Faqat tovushni eshitish",
      "Faqat rangni ko'rish"
    ],
    correctAnswer: "Odamlarning bir-birini, o'zini, ijtimoiy ob'ektlar va guruhlarni idrok etish, tushunish va baholash jarayoni"
  },
  {
    question: "**Kattalar yoshidagi krizislar** (masalan, 30, 40 yosh) nima bilan bog'liq?",
    options: [
      "Faqat jismoniy o'zgarishlar",
      "Hayot mazmunini qayta baholash, maqsadlarni o'zgartirish, shaxsiy va professional o'zlikni izlash",
      "Faqat temperament o'zgarishi",
      "Faqat ovqatlanish"
    ],
    correctAnswer: "Hayot mazmunini qayta baholash, maqsadlarni o'zgartirish, shaxsiy va professional o'zlikni izlash"
  },
  {
    question: "**Shaxsning yo'nalganligi** (Napravlennost lichnosti) nima?",
    options: [
      "Faqat yugurish",
      "Ehtiyojlar, qiziqishlar, e'tiqodlar va ideallar tizimi orqali belgilanadigan, shaxsning faoliyatini boshqaruvchi motivlar majmui",
      "Faqat o'ylash",
      "Faqat harakat"
    ],
    correctAnswer: "Ehtiyojlar, qiziqishlar, e'tiqodlar va ideallar tizimi orqali belgilanadigan, shaxsning faoliyatini boshqaruvchi motivlar majmui"
  },
  {
    question: "**Kichik maktab yoshi** (6-11 yosh) uchun asosiy faoliyat turi?",
    options: [
      "O'yin",
      "O'qish (o'rganish)",
      "Mehnat",
      "Muloqot"
    ],
    correctAnswer: "O'qish (o'rganish)"
  },
  {
    question: "**Muloqotning interaktiv tomoni** nima?",
    options: [
      "Faqat tushunish",
      "Odamlarning bir-biriga ta'sir o'tkazishi, harakatlarni tashkil etish va hamkorlik qilish",
      "Faqat axborot almashish",
      "Faqat baholash"
    ],
    correctAnswer: "Odamlarning bir-biriga ta'sir o'tkazishi, harakatlarni tashkil etish va hamkorlik qilish"
  },
  {
    question: "**O'z-o'zini baholash** (Samootsenka) nima?",
    options: [
      "Faqat boshqalarning bahosi",
      "Shaxsning o'z qobiliyatlari, fazilatlari, yutuqlari va kamchiliklariga beradigan subyektiv bahosi",
      "Faqat maktab bahosi",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "Shaxsning o'z qobiliyatlari, fazilatlari, yutuqlari va kamchiliklariga beradigan subyektiv bahosi"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarida **'Didaktik o'yinlar'**ning asosiy maqsadi nima?",
    options: [
      "Faqat vaqtni behuda o'tkazish",
      "O'quv materialini o'yin orqali qiziqarli o'zlashtirish va motivatsiyani oshirish",
      "Faqat baholash",
      "Faqat uy vazifasi berish"
    ],
    correctAnswer: "O'quv materialini o'yin orqali qiziqarli o'zlashtirish va motivatsiyani oshirish"
  },
  {
    question: "Ta'limda **kouching (Coaching)** qanday faoliyat turi?",
    options: [
      "Faqat ma'ruza o'qish",
      "O'quvchining ichki resurslarini ochishga, maqsadlarini aniqlashga va mustaqil harakat qilishga yo'naltirish",
      "Faqat jazolash",
      "Faqat test yechish"
    ],
    correctAnswer: "O'quvchining ichki resurslarini ochishga, maqsadlarini aniqlashga va mustaqil harakat qilishga yo'naltirish"
  },
  {
    question: "AKT yordamida **'Blended Learning'**ning qanday afzalligi bor?",
    options: [
      "Faqat o'qituvchining ishini kamaytirish",
      "An'anaviy ta'limning ijtimoiy muloqotini masofaviy ta'limning moslashuvchanligi bilan birlashtirish",
      "Faqat narxni tushirish",
      "Faqat qog'oz ishlarini yo'qotish"
    ],
    correctAnswer: "An'anaviy ta'limning ijtimoiy muloqotini masofaviy ta'limning moslashuvchanligi bilan birlashtirish"
  },
  {
    question: "Innovatsion ta'limda **'Refleksiya'** nimani anglatadi?",
    options: [
      "Faqat yozma ish",
      "O'quvchining o'z o'rganish jarayonini, fikrlarini va erishilgan natijalarini tahlil qilishi",
      "Faqat darslikni o'qish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "O'quvchining o'z o'rganish jarayonini, fikrlarini va erishilgan natijalarini tahlil qilishi"
  },
  {
    question: "Pedagogik texnologiyalarining **'Tizimli yondashuv'** prinsipi nima?",
    options: [
      "Faqat bir qismga e'tibor berish",
      "Ta'lim jarayonini yagona, izchil va o'zaro bog'liq komponentlar (maqsad, mazmun, metod, natija) majmui sifatida ko'rish",
      "Faqat darslikni almashtirish",
      "Faqat texnologiyani qo'llash"
    ],
    correctAnswer: "Ta'lim jarayonini yagona, izchil va o'zaro bog'liq komponentlar (maqsad, mazmun, metod, natija) majmui sifatida ko'rish"
  },
  {
    question: "Ta'limda **'Keys-stadi' (Case Study)** metodi nima uchun qo'llaniladi?",
    options: [
      "Faqat yodlash uchun",
      "Talabalarda muammoli vaziyatlarni tahlil qilish, tanqidiy fikrlash va qaror qabul qilish ko'nikmalarini rivojlantirish",
      "Faqat ma'ruza o'qish uchun",
      "Faqat test yechish uchun"
    ],
    correctAnswer: "Talabalarda muammoli vaziyatlarni tahlil qilish, tanqidiy fikrlash va qaror qabul qilish ko'nikmalarini rivojlantirish"
  },
  {
    question: "Innovatsion ta'limda **'Interfaol metodlar'**ning ahamiyati?",
    options: [
      "Faqat vaqtni tejash",
      "O'quvchilarning faolligini oshirish, bilimni passiv qabul qilishdan faol ishtirok etishga o'tishni ta'minlash",
      "Faqat o'qituvchiga yukni kamaytirish",
      "Faqat yozma ishlarni ko'paytirish"
    ],
    correctAnswer: "O'quvchilarning faolligini oshirish, bilimni passiv qabul qilishdan faol ishtirok etishga o'tishni ta'minlash"
  },
  {
    question: "Masofaviy ta'limda **'LMS' (Learning Management System)** nima?",
    options: [
      "Faqat elektron kutubxona",
      "O'quv materiallarini joylash, topshiriqlarni boshqarish, baholash va o'quvchilar faoliyatini kuzatish uchun platforma",
      "Faqat videokonferensiya dasturi",
      "Faqat test yaratish dasturi"
    ],
    correctAnswer: "O'quv materiallarini joylash, topshiriqlarni boshqarish, baholash va o'quvchilar faoliyatini kuzatish uchun platforma"
  },
  {
    question: "Innovatsion ta'lim texnologiyalarida **'Simulyatsiya'**ning asosiy funksiyasi?",
    options: [
      "Faqat rasm chizish",
      "Murakkab, xavfli yoki qimmat real jarayonlarni sun'iy muhitda (kompyuterda) modelini yaratish va amaliyot o'tkazish",
      "Faqat ma'ruza yozish",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "Murakkab, xavfli yoki qimmat real jarayonlarni sun'iy muhitda (kompyuterda) modelini yaratish va amaliyot o'tkazish"
  },
  {
    question: "Ta'limda **'Proyekt metodi'**ning asosiy bosqichlari?",
    options: [
      "Faqat yozish va baholash",
      "Muammoni aniqlash, rejalashtirish, tadqiqot, loyihani amalga oshirish va taqdimot",
      "Faqat ma'ruza o'qish va test yechish",
      "Faqat uy vazifasi berish"
    ],
    correctAnswer: "Muammoni aniqlash, rejalashtirish, tadqiqot, loyihani amalga oshirish va taqdimot"
  },
  {
    question: "**'Flipped Classroom' (Teskari sinf)** modelining o'ziga xosligi nima?",
    options: [
      "Faqat guruhlarda ishlash",
      "Nazariy materialni (ma'ruzani) uyda o'rganish, sinfda esa amaliy mashg'ulot va muammolarni hal qilish",
      "Faqat o'qituvchi uy vazifasi bermaydi",
      "Faqat testlar ishlatiladi"
    ],
    correctAnswer: "Nazariy materialni (ma'ruzani) uyda o'rganish, sinfda esa amaliy mashg'ulot va muammolarni hal qilish"
  },
  {
    question: "Innovatsion ta'limda **'Tanqidiy fikrlash'**ni rivojlantirish uchun qanday metodlar samarali?",
    options: [
      "Faqat yodlash",
      "Munozara, Sokratik savol-javob, Keys-stadi, Argumentatsiya tahlili",
      "Faqat ma'ruza tinglash",
      "Faqat oddiy test yechish"
    ],
    correctAnswer: "Munozara, Sokratik savol-javob, Keys-stadi, Argumentatsiya tahlili"
  },
  {
    question: "Pedagogik texnologiyaning **'Diagnostika'** bosqichida nima aniqlanadi?",
    options: [
      "Faqat darsning tugashi",
      "O'quvchilarning boshlang'ich bilim darajasi, qobiliyatlari va ehtiyojlari",
      "Faqat baholash usuli",
      "Faqat o'qituvchining tajribasi"
    ],
    correctAnswer: "O'quvchilarning boshlang'ich bilim darajasi, qobiliyatlari va ehtiyojlari"
  },
  {
    question: "Ta'limda **'Vizualizatsiya'** nima uchun muhim?",
    options: [
      "Faqat chizish",
      "Mavhum g'oyalar va murakkab ma'lumotlarni tushunishni osonlashtirish, eslab qolishni yaxshilash",
      "Faqat yozishni kamaytirish",
      "Faqat musiqa"
    ],
    correctAnswer: "Mavhum g'oyalar va murakkab ma'lumotlarni tushunishni osonlashtirish, eslab qolishni yaxshilash"
  },
  {
    question: "Innovatsion ta'limda **'Individuallashtirish'** nimani anglatadi?",
    options: [
      "Faqat tezkor o'qitish",
      "Har bir o'quvchining o'zlashtirish tezligi, uslubi va ehtiyojiga mos ravishda ta'lim mazmuni va metodlarini moslash",
      "Faqat sekin o'qitish",
      "Faqat barchaga bir xil dars berish"
    ],
    correctAnswer: "Har bir o'quvchining o'zlashtirish tezligi, uslubi va ehtiyojiga mos ravishda ta'lim mazmuni va metodlarini moslash"
  },
  {
    question: "AKT yordamida **'Virtual reallik (VR)'** qanday ta'lim imkoniyatini beradi?",
    options: [
      "Faqat o'yin o'ynash",
      "Xavfsiz va nazoratli muhitda amaliy ko'nikmalarni egallash, real jarayonlarni uch o'lchamli o'rganish",
      "Faqat ma'ruza tinglash",
      "Faqat yozish"
    ],
    correctAnswer: "Xavfsiz va nazoratli muhitda amaliy ko'nikmalarni egallash, real jarayonlarni uch o'lchamli o'rganish"
  },
  {
    question: "Ta'limda **'Munozara' (Debate)** metodining foydasi nima?",
    options: [
      "Faqat vaqtni o'tkazish",
      "O'quvchilarda fikrni himoya qilish, argumentatsiya, boshqalarni tinglash va muloqot madaniyatini rivojlantirish",
      "Faqat o'qituvchini eshitish",
      "Faqat o'qish"
    ],
    correctAnswer: "O'quvchilarda fikrni himoya qilish, argumentatsiya, boshqalarni tinglash va muloqot madaniyatini rivojlantirish"
  },
  {
    question: "Innovatsion ta'limda **'Avtomatik baholash'** tizimining afzalligi?",
    options: [
      "Faqat jazolash",
      "Baholashning obyektivligini oshirish, o'qituvchi vaqtini tejash va o'quvchiga tezkor qayta aloqa berish",
      "Faqat ma'ruza o'qish",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "Baholashning obyektivligini oshirish, o'qituvchi vaqtini tejash va o'quvchiga tezkor qayta aloqa berish"
  },
  {
    question: "Pedagogik texnologiyalarining **'Korreksiya'** bosqichida nima amalga oshiriladi?",
    options: [
      "Faqat maqsadni belgilash",
      "O'quv jarayoni natijalari va samaradorligini tahlil qilib, ta'lim metodikasiga zaruriy o'zgartirishlar kiritish",
      "Faqat test tuzish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "O'quv jarayoni natijalari va samaradorligini tahlil qilib, ta'lim metodikasiga zaruriy o'zgartirishlar kiritish"
  },
  {
    question: "Innovatsion ta'limda **'Muammoli ta'lim'**ning asosiy tamoyili nima?",
    options: [
      "Faqat ma'lumot berish",
      "O'quvchiga tayyor bilim bermasdan, uni muammoli vaziyatga solish va yechimni o'zi topishga undash",
      "Faqat yodlash",
      "Faqat uy vazifasi berish"
    ],
    correctAnswer: "O'quvchiga tayyor bilim bermasdan, uni muammoli vaziyatga solish va yechimni o'zi topishga undash"
  },
  {
    question: "AKT yordamida **'Bulutli texnologiyalar'** qanday imkoniyat beradi?",
    options: [
      "Faqat qurilmani buzish",
      "Ma'lumotlar va dasturlarga istalgan joydan, istalgan qurilmadan internet orqali kirish",
      "Faqat qog'oz ishlarini ko'paytirish",
      "Faqat test yechish"
    ],
    correctAnswer: "Ma'lumotlar va dasturlarga istalgan joydan, istalgan qurilmadan internet orqali kirish"
  },
  {
    question: "Ta'limda **'Aqliy hujum' (Brainstorming)** metodi nima uchun ishlatiladi?",
    options: [
      "Faqat baholash",
      "Qisqa vaqt ichida muammoni yechish uchun maksimal darajada yangi va kreativ g'oyalarni generatsiya qilish",
      "Faqat nazorat qilish",
      "Faqat yozish"
    ],
    correctAnswer: "Qisqa vaqt ichida muammoni yechish uchun maksimal darajada yangi va kreativ g'oyalarni generatsiya qilish"
  },
  {
    question: "Innovatsion ta'limda **'Mentorlik'**ning asosiy maqsadi nima?",
    options: [
      "Faqat jazolash",
      "Tajribali kishi (mentor) tomonidan yosh/tajribasiz shaxsga (menti) yo'nalish, maslahat va motivatsiya berish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "Tajribali kishi (mentor) tomonidan yosh/tajribasiz shaxsga (menti) yo'nalish, maslahat va motivatsiya berish"
  },
  {
    question: "Pedagogik texnologiyaning **'Nazorat' (Monitoring)** bosqichi nima?",
    options: [
      "Faqat darslik yaratish",
      "Ta'lim jarayonining borishi, o'quvchilarning faoliyati va o'zlashtirish natijalarini muntazam kuzatib borish",
      "Faqat ma'ruza o'qish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "Ta'lim jarayonining borishi, o'quvchilarning faoliyati va o'zlashtirish natijalarini muntazam kuzatib borish"
  },
  {
    question: "Ta'limda **'Portfoliyo'** qanday vazifani bajaradi?",
    options: [
      "Faqat darslikni saqlash",
      "O'quvchining o'zlashtirish, ijodkorlik va rivojlanish yutuqlari namunalari to'plami",
      "Faqat test yechish",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "O'quvchining o'zlashtirish, ijodkorlik va rivojlanish yutuqlari namunalari to'plami"
  },
  {
    question: "Innovatsion ta'limda **'Empatiya'** nimani anglatadi?",
    options: [
      "Faqat jazolash",
      "Boshqa insonning his-tuyg'ularini, holatini va nuqtai nazarini tushuna olish va hamdardlik bildirish",
      "Faqat ma'ruza o'qish",
      "Faqat bilimni o'lchash"
    ],
    correctAnswer: "Boshqa insonning his-tuyg'ularini, holatini va nuqtai nazarini tushuna olish va hamdardlik bildirish"
  },
  {
    question: "AKT yordamida **'O'z-o'zini baholash (Self-assessment)'**ning maqsadi?",
    options: [
      "Faqat o'qituvchiga yukni tushirish",
      "O'quvchining o'z kuchli va zaif tomonlarini tanqidiy baholash, javobgarlikni oshirish",
      "Faqat ma'ruza yozish",
      "Faqat test yechish"
    ],
    correctAnswer: "O'quvchining o'z kuchli va zaif tomonlarini tanqidiy baholash, javobgarlikni oshirish"
  },
  {
    question: "Ta'limda **'Role Playing' (Rolli o'yinlar)** nima uchun kerak?",
    options: [
      "Faqat o'yin o'ynash",
      "O'quvchilarda ijtimoiy, muloqot va vaziyatni tahlil qilish ko'nikmalarini rivojlantirish, nazariy bilimni amalda qo'llash",
      "Faqat ma'ruza tinglash",
      "Faqat yozish"
    ],
    correctAnswer: "O'quvchilarda ijtimoiy, muloqot va vaziyatni tahlil qilish ko'nikmalarini rivojlantirish, nazariy bilimni amalda qo'llash"
  },
  {
    question: "Innovatsion ta'limda **'O'qituvchining kompetentligi'**ga nimalar kiradi?",
    options: [
      "Faqat fan bilimi",
      "Metodik, psixologik-pedagogik, ijtimoiy va axborot-kommunikatsiya (AKT) kompetentligi",
      "Faqat darslikni yodlash",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "Metodik, psixologik-pedagogik, ijtimoiy va axborot-kommunikatsiya (AKT) kompetentligi"
  },
  {
    question: "Pedagogik texnologiyada **'Loyihalash'** bosqichi nima?",
    options: [
      "Faqat test yechish",
      "Ta'lim maqsadlaridan boshlab, o'quv materialini, metodlarni va baholash usullarini tizimli rejalashtirish",
      "Faqat ma'ruza o'qish",
      "Faqat uy vazifasi berish"
    ],
    correctAnswer: "Ta'lim maqsadlaridan boshlab, o'quv materialini, metodlarni va baholash usullarini tizimli rejalashtirish"
  },
  {
    question: "Ta'limda **'Tadqiqot metodi'**ning asosiy maqsadi?",
    options: [
      "Faqat darslikni o'qish",
      "O'quvchilarda izlanish, ma'lumotlarni yig'ish, tahlil qilish va mustaqil xulosalar chiqarish ko'nikmasini shakllantirish",
      "Faqat ma'ruza tinglash",
      "Faqat jazolash"
    ],
    correctAnswer: "O'quvchilarda izlanish, ma'lumotlarni yig'ish, tahlil qilish va mustaqil xulosalar chiqarish ko'nikmasini shakllantirish"
  },
  {
    question: "Innovatsion ta'limda **'Qayta aloqa' (Feedback)** qanday bo'lishi kerak?",
    options: [
      "Faqat umumiy",
      "O'z vaqtida, konstruktiv, aniq va aniq harakatlarga yo'naltirilgan",
      "Faqat baho",
      "Faqat jazolash"
    ],
    correctAnswer: "O'z vaqtida, konstruktiv, aniq va aniq harakatlarga yo'naltirilgan"
  },
  {
    question: "AKT yordamida **'Onlayn testlash'**ning afzalligi nima?",
    options: [
      "Faqat yozish",
      "Tezkor tekshirish, natijalarni avtomatik tahlil qilish, baholashning obyektivligi va vaqtni tejash",
      "Faqat ma'ruza",
      "Faqat rasm chizish"
    ],
    correctAnswer: "Tezkor tekshirish, natijalarni avtomatik tahlil qilish, baholashning obyektivligi va vaqtni tejash"
  },
  {
    question: "Ta'limda **'O'qitishning differensiallashuvi'** nima?",
    options: [
      "Faqat qiyin vazifa berish",
      "O'quvchilarning tayyorgarligi, qiziqishi va o'zlashtirish tezligiga qarab ularga turli darajadagi topshiriqlar berish",
      "Faqat oson vazifa berish",
      "Faqat bir xil dars berish"
    ],
    correctAnswer: "O'quvchilarning tayyorgarligi, qiziqishi va o'zlashtirish tezligiga qarab ularga turli darajadagi topshiriqlar berish"
  },
  {
    question: "Innovatsion ta'limda **'O'quv motivatsiyasi'**ni oshirishning samarali yo'llari?",
    options: [
      "Faqat jazolash",
      "Qiziqarli topshiriqlar, muvaffaqiyat hissini yaratish, maqsadni aniqlash va o'yin texnologiyalaridan foydalanish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "Qiziqarli topshiriqlar, muvaffaqiyat hissini yaratish, maqsadni aniqlash va o'yin texnologiyalaridan foydalanish"
  },
  {
    question: "Pedagogik texnologiyaning **'Metodik ta'minot'**iga nimalar kiradi?",
    options: [
      "Faqat bino",
      "Darsliklar, o'quv qo'llanmalari, didaktik materiallar, o'qitish uslubiy tavsiyalari",
      "Faqat kompyuterlar",
      "Faqat o'qituvchilar"
    ],
    correctAnswer: "Darsliklar, o'quv qo'llanmalari, didaktik materiallar, o'qitish uslubiy tavsiyalari"
  },
  {
    question: "Ta'limda **'Muloqot kompetentligi'** nima?",
    options: [
      "Faqat yozish",
      "Turli odamlar bilan samarali aloqa o'rnata olish, fikr almashish va hamkorlik qila olish qobiliyati",
      "Faqat o'qish",
      "Faqat rasm chizish"
    ],
    correctAnswer: "Turli odamlar bilan samarali aloqa o'rnata olish, fikr almashish va hamkorlik qila olish qobiliyati"
  },
  {
    question: "Innovatsion ta'limda **'Aqlli sinf' (Smart Classroom)** nima?",
    options: [
      "Faqat oddiy sinf",
      "Interfaol texnologiyalar, multimedia vositalari va internetga ulangan qurilmalar bilan jihozlangan o'quv xonasi",
      "Faqat kitob saqlanadigan xona",
      "Faqat sport zali"
    ],
    correctAnswer: "Interfaol texnologiyalar, multimedia vositalari va internetga ulangan qurilmalar bilan jihozlangan o'quv xonasi"
  },
  {
    question: "AKT yordamida **'Onlayn kurslar' (MOOCs)**ning afzalligi nima?",
    options: [
      "Faqat qimmatligi",
      "Katta auditoriya uchun ochiqligi, moslashuvchan jadval, turli mavzularni o'rganish imkoniyati",
      "Faqat yozish",
      "Faqat test yechish"
    ],
    correctAnswer: "Katta auditoriya uchun ochiqligi, moslashuvchan jadval, turli mavzularni o'rganish imkoniyati"
  },
  {
    question: "Ta'limda **'O'quv materialining tuzilishi'** qanday tamoyilga asoslanishi kerak?",
    options: [
      "Faqat uzunlik",
      "Tizimlilik, mantiqiylik, izchillik va o'zlashtirishga qulaylik",
      "Faqat qisqalik",
      "Faqat qiyinlik"
    ],
    correctAnswer: "Tizimlilik, mantiqiylik, izchillik va o'zlashtirishga qulaylik"
  },
  {
    question: "Innovatsion ta'limda **'Xatolardan o'rganish'** konsepsiyasi nima?",
    options: [
      "Faqat jazolash",
      "Xatoni bilimlarni chuqurlashtirish va rivojlanish uchun imkoniyat deb bilish, ularni tahlil qilish",
      "Faqat baho qo'yish",
      "Faqat ma'ruza o'qish"
    ],
    correctAnswer: "Xatoni bilimlarni chuqurlashtirish va rivojlanish uchun imkoniyat deb bilish, ularni tahlil qilish"
  },
  {
    question: "Pedagogik texnologiyada **'Operatsional maqsad'** nima?",
    options: [
      "Faqat umumiy g'oya",
      "O'quvchida dars natijasida shakllanadigan, aniq o'lchanadigan va kuzatiladigan harakat",
      "Faqat o'qituvchining maqsadi",
      "Faqat darslikning nomi"
    ],
    correctAnswer: "O'quvchida dars natijasida shakllanadigan, aniq o'lchanadigan va kuzatiladigan harakat"
  },
  {
    question: "Ta'limda **'Guruhli ishlash'**ning asosiy afzalligi nima?",
    options: [
      "Faqat bir kishi ishlaydi",
      "Hamkorlik, muloqot, turli fikrlarni tinglash va bir-biridan o'rganish ko'nikmalarini rivojlantirish",
      "Faqat o'qituvchi gapiradi",
      "Faqat yozish"
    ],
    correctAnswer: "Hamkorlik, muloqot, turli fikrlarni tinglash va bir-biridan o'rganish ko'nikmalarini rivojlantirish"
  },
  {
    question: "Innovatsion ta'limda **'Kompetentlik'** deganda nimani tushunasiz?",
    options: [
      "Faqat bilim",
      "Muayyan faoliyatni samarali amalga oshirish uchun bilim, ko'nikma, malaka, qadriyat va shaxsiy sifatlarning majmui",
      "Faqat ma'lumot",
      "Faqat jazolash"
    ],
    correctAnswer: "Muayyan faoliyatni samarali amalga oshirish uchun bilim, ko'nikma, malaka, qadriyat va shaxsiy sifatlarning majmui"
  },
  {
    question: "AKT yordamida **'Videokonferensiya'** nima?",
    options: [
      "Faqat rasm",
      "Internet orqali real vaqt rejimida bir nechta ishtirokchi o'rtasida ovoz, video va matnli muloqotni tashkil etish",
      "Faqat yozish",
      "Faqat musiqa"
    ],
    correctAnswer: "Internet orqali real vaqt rejimida bir nechta ishtirokchi o'rtasida ovoz, video va matnli muloqotni tashkil etish"
  },
  {
    question: "Ta'limda **'Interaktiv doska'**ning asosiy o'rni?",
    options: [
      "Faqat qora doska",
      "Vizualizatsiya, yozish, rasm chizish, internetga chiqish va multimedia resurslarini boshqarishni birlashtirish",
      "Faqat o'qituvchi ma'ruzasi",
      "Faqat test yechish"
    ],
    correctAnswer: "Vizualizatsiya, yozish, rasm chizish, internetga chiqish va multimedia resurslarini boshqarishni birlashtirish"
  },
  {
    question: "Innovatsion ta'limda **'Adaptiv o'qitish'** nima?",
    options: [
      "Faqat tez o'qitish",
      "O'qitish dasturining har bir o'quvchining joriy bilim darajasi va o'rganish tempiga avtomatik moslashuvi",
      "Faqat sekin o'qitish",
      "Faqat barchaga bir xil dars berish"
    ],
    correctAnswer: "O'qitish dasturining har bir o'quvchining joriy bilim darajasi va o'rganish tempiga avtomatik moslashuvi"
  },
  {
    question: "Pedagogik texnologiyaning **'Qayta aloqa tizimi'** nima?",
    options: [
      "Faqat jazolash",
      "O'quv jarayonining natijalari va o'quvchilarning xatolari haqida ularga va o'qituvchiga ma'lumot berish mexanizmi",
      "Faqat ma'ruza o'qish",
      "Faqat darslik yaratish"
    ],
    correctAnswer: "O'quv jarayonining natijalari va o'quvchilarning xatolari haqida ularga va o'qituvchiga ma'lumot berish mexanizmi"
  },
  {
    question: "Ta'limda **'Loyihaviy guruhlar'** qanday tashkil etiladi?",
    options: [
      "Faqat o'qituvchi tanlaydi",
      "Turli bilim, ko'nikma va qiziqishlarga ega bo'lgan o'quvchilardan, muammoni yechish uchun birlashtirish",
      "Faqat bir xil odamlar",
      "Faqat test yechish uchun"
    ],
    correctAnswer: "Turli bilim, ko'nikma va qiziqishlarga ega bo'lgan o'quvchilardan, muammoni yechish uchun birlashtirish"
  },
  {
    question: "Innovatsion ta'limda **'O'qituvchi-fasilitator'**ning roli nima?",
    options: [
      "Faqat ma'ruza o'qish",
      "O'quvchilarga o'rganish jarayonini tashkil etishda va muammolarni yechishda yordam berish, yo'naltirish",
      "Faqat baho qo'yish",
      "Faqat jazolash"
    ],
    correctAnswer: "O'quvchilarga o'rganish jarayonini tashkil etishda va muammolarni yechishda yordam berish, yo'naltirish"
  },
  {
    question: "AKT yordamida **'Augmented Reality (AR)' (Kengaytirilgan reallik)** nima?",
    options: [
      "Faqat virtual dunyo",
      "Real dunyo tasviriga kompyuter yaratgan raqamli axborotni (video, 3D modellar) qo'shish",
      "Faqat musiqa",
      "Faqat yozish"
    ],
    correctAnswer: "Real dunyo tasviriga kompyuter yaratgan raqamli axborotni (video, 3D modellar) qo'shish"
  },
  {
    question: "Ta'limda **'Kompetentlikka asoslangan ta'lim'** nimani anglatadi?",
    options: [
      "Faqat nazariya",
      "Bilimlarni o'zlashtirishdan ko'ra, ularni amalda qo'llash qobiliyatiga (kompetentlikka) e'tibor berish",
      "Faqat yodlash",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Bilimlarni o'zlashtirishdan ko'ra, ularni amalda qo'llash qobiliyatiga (kompetentlikka) e'tibor berish"
  },
  {
    question: "Innovatsion ta'limda **'O'quv jarayonining dinamikligi'** nima?",
    options: [
      "Faqat bir xil dars",
      "Ta'limning o'zgaruvchan ehtiyojlar, yangi texnologiyalar va o'quvchilarning fikrlariga mos ravishda doimiy yangilanib turishi",
      "Faqat qoidalar",
      "Faqat eskicha usul"
    ],
    correctAnswer: "Ta'limning o'zgaruvchan ehtiyojlar, yangi texnologiyalar va o'quvchilarning fikrlariga mos ravishda doimiy yangilanib turishi"
  },
  {
    question: "Pedagogik texnologiyaning **'Qaytar aloqa' (Monitoring va Korreksiya)** maqsadi nima?",
    options: [
      "Faqat jazolash",
      "O'quv jarayonini boshqarish, natijalarni yaxshilash va maqsadlarga erishishni ta'minlash uchun ma'lumot yig'ish va tuzatish kiritish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "O'quv jarayonini boshqarish, natijalarni yaxshilash va maqsadlarga erishishni ta'minlash uchun ma'lumot yig'ish va tuzatish kiritish"
  },
  {
    question: "Ta'limda **'Individual ta'lim yo'nalishi'**ni yaratish nima?",
    options: [
      "Faqat umumiy darslik",
      "Har bir o'quvchining maqsadlari, bilim darajasi va qiziqishiga mos ravishda uning o'rganish yo'lini belgilash",
      "Faqat bir xil test",
      "Faqat guruhli ishlash"
    ],
    correctAnswer: "Har bir o'quvchining maqsadlari, bilim darajasi va qiziqishiga mos ravishda uning o'rganish yo'lini belgilash"
  },
  {
    question: "Innovatsion ta'limda **'Hamkorlik (Collaboration)'** ko'nikmasi nima uchun muhim?",
    options: [
      "Faqat yozish",
      "Zamonaviy mehnat bozorida va ijtimoiy hayotda muvaffaqiyatga erishish uchun guruhda birga ishlash, fikr almashish va yechim topish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "Zamonaviy mehnat bozorida va ijtimoiy hayotda muvaffaqiyatga erishish uchun guruhda birga ishlash, fikr almashish va yechim topish"
  },
  {
    question: "AKT yordamida **'Mobil o'rganish (M-learning)'** nima?",
    options: [
      "Faqat katta kompyuterda",
      "Mobil qurilmalar (smartfon, planshet) yordamida istalgan joyda va vaqtda ta'lim olish imkoniyati",
      "Faqat yozish",
      "Faqat musiqa"
    ],
    correctAnswer: "Mobil qurilmalar (smartfon, planshet) yordamida istalgan joyda va vaqtda ta'lim olish imkoniyati"
  },
  {
    question: "Ta'limda **'Axborot-kommunikatsiya texnologiyalari (AKT)'**ning asosiy maqsadi?",
    options: [
      "Faqat internetda o'tirish",
      "Ta'lim mazmunini boyitish, o'qitish metodlarini diversifikatsiya qilish va ta'lim samaradorligini oshirish",
      "Faqat yozish",
      "Faqat musiqa"
    ],
    correctAnswer: "Ta'lim mazmunini boyitish, o'qitish metodlarini diversifikatsiya qilish va ta'lim samaradorligini oshirish"
  },
  {
    question: "Innovatsion ta'limda **'Kreativlik'**ning o'rni?",
    options: [
      "Faqat yodlash",
      "Muammolarga nostandart yechimlar topish, yangi g'oyalar yaratish va ijodiy yondashuvni rivojlantirish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "Muammolarga nostandart yechimlar topish, yangi g'oyalar yaratish va ijodiy yondashuvni rivojlantirish"
  },
  {
    question: "Pedagogik texnologiyalarining **'Texnologik xarita'**si nima?",
    options: [
      "Faqat bino chizmasi",
      "Darsni o'tish jarayonining bosqichlari, foydalaniladigan metodlar, vositalar va vaqtini aniq ko'rsatuvchi hujjat (loyiha)",
      "Faqat baholash usuli",
      "Faqat o'quvchilar ro'yxati"
    ],
    correctAnswer: "Darsni o'tish jarayonining bosqichlari, foydalaniladigan metodlar, vositalar va vaqtini aniq ko'rsatuvchi hujjat (loyiha)"
  },
  {
    question: "Ta'limda **'Debat (Munozara)'** metodi qaysi ko'nikmalarni rivojlantiradi?",
    options: [
      "Faqat eshitish",
      "Argumentatsiya, tanqidiy fikrlash, notiqlik, o'z fikrini asoslash va xulosalar chiqarish",
      "Faqat yozish",
      "Faqat rasm chizish"
    ],
    correctAnswer: "Argumentatsiya, tanqidiy fikrlash, notiqlik, o'z fikrini asoslash va xulosalar chiqarish"
  },
  {
    question: "Innovatsion ta'limda **'Mustaqil o'rganish ko'nikmasi'** nima?",
    options: [
      "Faqat uy vazifasi",
      "O'quvchining o'z o'rganish ehtiyojlarini aniqlash, resurslarni topish va jarayonni o'zi boshqarish qobiliyati",
      "Faqat ma'ruza tinglash",
      "Faqat test yechish"
    ],
    correctAnswer: "O'quvchining o'z o'rganish ehtiyojlarini aniqlash, resurslarni topish va jarayonni o'zi boshqarish qobiliyati"
  },
  {
    question: "AKT yordamida **'Geymifikatsiya (Gamification)'**ning ta'limdagi maqsadi?",
    options: [
      "Faqat o'yin o'ynash",
      "Ta'lim jarayoniga o'yin elementlarini (ballar, darajalar, mukofotlar) kiritish orqali motivatsiya va jalb qilishni oshirish",
      "Faqat musiqa",
      "Faqat yozish"
    ],
    correctAnswer: "Ta'lim jarayoniga o'yin elementlarini (ballar, darajalar, mukofotlar) kiritish orqali motivatsiya va jalb qilishni oshirish"
  },
  {
    question: "Ta'limda **'Ko'nikma'** nima?",
    options: [
      "Faqat bilim",
      "Amaliy harakatni ongli ravishda, ammo avtomatlashmagan holda, malaka darajasiga erishish yo'lidagi bajarish qobiliyati",
      "Faqat xarakter",
      "Faqat temperament"
    ],
    correctAnswer: "Amaliy harakatni ongli ravishda, ammo avtomatlashmagan holda, malaka darajasiga erishish yo'li"
  },
  {
    question: "Innovatsion ta'limda **'Virtual ekskursiya'** nima uchun ishlatiladi?",
    options: [
      "Faqat dam olish",
      "Geografik yoki tarixiy jihatdan uzoq joylarga, xavfsiz va arzon tarzda virtual sayohat qilish imkoniyatini berish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "Geografik yoki tarixiy jihatdan uzoq joylarga, xavfsiz va arzon tarzda virtual sayohat qilish imkoniyatini berish"
  },
  {
    question: "Pedagogik texnologiyaning **'Analiz'** bosqichi nima?",
    options: [
      "Faqat sintez",
      "Ta'lim ehtiyojlarini, o'quvchilarning xususiyatlarini, muammolarni va mavjud resurslarni o'rganish",
      "Faqat jazolash",
      "Faqat baholash"
    ],
    correctAnswer: "Ta'lim ehtiyojlarini, o'quvchilarning xususiyatlarini, muammolarni va mavjud resurslarni o'rganish"
  },
  {
    question: "Ta'limda **'Interfaol ma'ruza'** qanday tashkil etiladi?",
    options: [
      "Faqat o'qituvchi gapiradi",
      "O'qituvchining ma'ruzasi o'quvchilar bilan doimiy savol-javob, munozara va kichik amaliy topshiriqlar bilan almashinishi",
      "Faqat yozish",
      "Faqat test yechish"
    ],
    correctAnswer: "O'qituvchining ma'ruzasi o'quvchilar bilan doimiy savol-javob, munozara va kichik amaliy topshiriqlar bilan almashinishi"
  },
  {
    question: "Innovatsion ta'limda **'4K' ko'nikmalari** nima?",
    options: [
      "Faqat sport",
      "Kreativlik (Creativity), Tanqidiy fikrlash (Critical Thinking), Hamkorlik (Collaboration), Muloqot (Communication)",
      "Faqat yozish",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Kreativlik (Creativity), Tanqidiy fikrlash (Critical Thinking), Hamkorlik (Collaboration), Muloqot (Communication)"
  },
  {
    question: "AKT yordamida **'O'quv platformalari (LMS)'**ning asosiy vazifasi?",
    options: [
      "Faqat musiqa",
      "O'quv jarayonini boshqarish, kontentni yetkazish, topshiriqlarni yig'ish va baholashni avtomatlashtirish",
      "Faqat o'yin",
      "Faqat rasm chizish"
    ],
    correctAnswer: "O'quv jarayonini boshqarish, kontentni yetkazish, topshiriqlarni yig'ish va baholashni avtomatlashtirish"
  },
  {
    question: "Ta'limda **'Malaka'** nima?",
    options: [
      "Faqat bilim",
      "Amaliy harakatni ongli nazoratsiz, tez va aniq bajarish (avtomatlashgan ko'nikma)",
      "Faqat xarakter",
      "Faqat temperament"
    ],
    correctAnswer: "Amaliy harakatni ongli nazoratsiz, tez va aniq bajarish (avtomatlashgan ko'nikma)"
  },
  {
    question: "Innovatsion ta'limda **'Dizayn fikrlash (Design Thinking)'** nima?",
    options: [
      "Faqat rasm chizish",
      "Murakkab muammolarni inson ehtiyojlariga e'tibor bergan holda ijodiy va prototip usulida yechish metodologiyasi",
      "Faqat ma'ruza",
      "Faqat test yechish"
    ],
    correctAnswer: "Murakkab muammolarni inson ehtiyojlariga e'tibor bergan holda ijodiy va prototip usulida yechish metodologiyasi"
  },
  {
    question: "Pedagogik texnologiyaning **'Qo'llash (Implementatsiya)'** bosqichi nima?",
    options: [
      "Faqat rejalashtirish",
      "Yaratilgan o'quv modelini, metodlar va vositalarni amalda sinf sharoitida qo'llash",
      "Faqat baholash",
      "Faqat tahlil"
    ],
    correctAnswer: "Yaratilgan o'quv modelini, metodlar va vositalarni amalda sinf sharoitida qo'llash"
  },
  {
    question: "Ta'limda **'O'z-o'zini rivojlantirish'** nima?",
    options: [
      "Faqat darslik o'qish",
      "Shaxsning o'z kamchilik va ehtiyojlarini anglagan holda, bilimi, ko'nikmasi va shaxsiy sifatlarini oshirishga qaratilgan ongli harakati",
      "Faqat jazolash",
      "Faqat baholash"
    ],
    correctAnswer: "Shaxsning o'z kamchilik va ehtiyojlarini anglagan holda, bilimi, ko'nikmasi va shaxsiy sifatlarini oshirishga qaratilgan ongli harakati"
  },
  {
    question: "Innovatsion ta'limda **'Masofaviy ta'lim'**ning asosiy muammosi?",
    options: [
      "Faqat darslik etishmasligi",
      "Texnik ta'minotning bir xil emasligi, ijtimoiy muloqotning kamayishi, o'quvchining yuqori darajadagi mustaqillik talab qilishi",
      "Faqat qimmatligi",
      "Faqat uzoqlik"
    ],
    correctAnswer: "Texnik ta'minotning bir xil emasligi, ijtimoiy muloqotning kamayishi, o'quvchining yuqori darajadagi mustaqillik talab qilishi"
  },
  {
    question: "AKT yordamida **'Crowdsourcing'**ning ta'limdagi o'rni?",
    options: [
      "Faqat ma'ruza",
      "Katta guruh (ko'pincha onlayn) ishtirokchilari tomonidan ma'lumot, g'oyalar yoki vazifalarni bajarishda hissa qo'shish",
      "Faqat test yechish",
      "Faqat musiqa"
    ],
    correctAnswer: "Katta guruh (ko'pincha onlayn) ishtirokchilari tomonidan ma'lumot, g'oyalar yoki vazifalarni bajarishda hissa qo'shish"
  },
  {
    question: "Ta'limda **'Metodologiya'** nima?",
    options: [
      "Faqat darslik",
      "Ta'lim jarayonini tashkil etish, amalga oshirish va baholashning umumiy tamoyillari, nazariy yondashuvlari va uslublari majmui",
      "Faqat texnika",
      "Faqat baho"
    ],
    correctAnswer: "Ta'lim jarayonini tashkil etish, amalga oshirish va baholashning umumiy tamoyillari, nazariy yondashuvlari va uslublari majmui"
  },
  {
    question: "Innovatsion ta'limda **'Taqdimot (Presentation)'** texnologiyasi maqsadi?",
    options: [
      "Faqat gapirish",
      "Murakkab ma'lumotni vizual va ixcham shaklda yetkazish, auditoriyaning e'tiborini jalb qilish",
      "Faqat yozish",
      "Faqat test yechish"
    ],
    correctAnswer: "Murakkab ma'lumotni vizual va ixcham shaklda yetkazish, auditoriyaning e'tiborini jalb qilish"
  },
  {
    question: "Pedagogik texnologiyada **'Amaliy natija'** nima?",
    options: [
      "Faqat bilim",
      "O'quvchi tomonidan o'zlashtirilgan va amalda qo'llanilishi mumkin bo'lgan aniq ko'nikma yoki mahsulot",
      "Faqat ma'ruza",
      "Faqat baho"
    ],
    correctAnswer: "O'quvchi tomonidan o'zlashtirilgan va amalda qo'llanilishi mumkin bo'lgan aniq ko'nikma yoki mahsulot"
  },
  {
    question: "Ta'limda **'Ko'rgazmali qurollar'**ning asosiy funksiyasi?",
    options: [
      "Faqat rasm",
      "Mavhum narsalar, jarayonlar yoki tushunchalarni vizual tasvirlash orqali tushunishni osonlashtirish",
      "Faqat yozish",
      "Faqat musiqa"
    ],
    correctAnswer: "Mavhum narsalar, jarayonlar yoki tushunchalarni vizual tasvirlash orqali tushunishni osonlashtirish"
  },
  {
    question: "Innovatsion ta'limda **'Pedagogik tashxis'** nima?",
    options: [
      "Faqat tibbiy",
      "O'quvchining rivojlanish darajasi, qobiliyatlari, o'rganishdagi qiyinchiliklari va muvaffaqiyatlarini o'rganish va aniqlash",
      "Faqat jazolash",
      "Faqat ma'ruza"
    ],
    correctAnswer: "O'quvchining rivojlanish darajasi, qobiliyatlari, o'rganishdagi qiyinchiliklari va muvaffaqiyatlarini o'rganish va aniqlash"
  },
  {
    question: "AKT yordamida **'Bloglar va Vikilar'**ning ta'limdagi ahamiyati?",
    options: [
      "Faqat vaqt o'tkazish",
      "O'quvchilarning birgalikda (kollaborativ) ma'lumot yaratishi, almashishi va bilimni kengaytirishi",
      "Faqat musiqa",
      "Faqat o'yin"
    ],
    correctAnswer: "O'quvchilarning birgalikda (kollaborativ) ma'lumot yaratishi, almashishi va bilimni kengaytirishi"
  },
  {
    question: "Ta'limda **'Bilish' (Kognitiv) jarayonlar** nima?",
    options: [
      "Faqat yugurish",
      "Axborotni qabul qilish, qayta ishlash, eslab qolish va undan foydalanish bilan bog'liq ruhiy jarayonlar (sezgi, idrok, xotira, tafakkur)",
      "Faqat jazolash",
      "Faqat ovqatlanish"
    ],
    correctAnswer: "Axborotni qabul qilish, qayta ishlash, eslab qolish va undan foydalanish bilan bog'liq ruhiy jarayonlar (sezgi, idrok, xotira, tafakkur)"
  },
  {
    question: "Innovatsion ta'limda **'Kompleks yondashuv'** nima?",
    options: [
      "Faqat bir metod",
      "Ta'lim maqsadlariga erishish uchun bir nechta turli metodlar, vositalar va shakllarni birgalikda, tizimli ravishda qo'llash",
      "Faqat ma'ruza",
      "Faqat test"
    ],
    correctAnswer: "Ta'lim maqsadlariga erishish uchun bir nechta turli metodlar, vositalar va shakllarni birgalikda, tizimli ravishda qo'llash"
  },
  {
    question: "Pedagogik texnologiyaning **'Samaradorlik'** ko'rsatkichi nima?",
    options: [
      "Faqat baho",
      "Belgilangan natijalarga erishish va sarflangan resurslar (vaqt, pul, mehnat) o'rtasidagi nisbat",
      "Faqat o'qituvchi ishi",
      "Faqat darslik"
    ],
    correctAnswer: "Belgilangan natijalarga erishish va sarflangan resurslar (vaqt, pul, mehnat) o'rtasidagi nisbat"
  },
  {
    question: "Ta'limda **'O'qitishning o'ziga xosligi'** (Personalizatsiya) nima?",
    options: [
      "Faqat guruh bilan ishlash",
      "O'qitishni har bir o'quvchining shaxsiy maqsadlari, qiziqishlari va o'rganish tezligiga to'liq moslashtirish",
      "Faqat bir xil dars berish",
      "Faqat test yechish"
    ],
    correctAnswer: "O'qitishni har bir o'quvchining shaxsiy maqsadlari, qiziqishlari va o'rganish tezligiga to'liq moslashtirish"
  },
  {
    question: "Innovatsion ta'limda **'O'quv resurslari'**ning zamonaviy turlari?",
    options: [
      "Faqat qog'oz kitoblar",
      "Elektron darsliklar, MOOC, video ma'ruzalar, simulyatsiyalar, virtual labaratoriyalar",
      "Faqat qora doska",
      "Faqat qalam va daftar"
    ],
    correctAnswer: "Elektron darsliklar, MOOC, video ma'ruzalar, simulyatsiyalar, virtual labaratoriyalar"
  },
  {
    question: "AKT yordamida **'Learning Analytics'** (Ta'lim tahlili) nima?",
    options: [
      "Faqat baho qo'yish",
      "O'quvchilarning faoliyatidan yig'ilgan ma'lumotlarni tahlil qilish orqali o'rganish jarayonini optimallashtirish va prognoz qilish",
      "Faqat ma'ruza",
      "Faqat musiqa"
    ],
    correctAnswer: "O'quvchilarning faoliyatidan yig'ilgan ma'lumotlarni tahlil qilish orqali o'rganish jarayonini optimallashtirish va prognoz qilish"
  },
  {
    question: "Ta'limda **'O'zaro baholash' (Peer-assessment)** nima?",
    options: [
      "Faqat o'qituvchi baholaydi",
      "O'quvchilarning bir-birlarining ishlarini belgilangan mezonlar asosida baholashi",
      "Faqat ma'ruza",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "O'quvchilarning bir-birlarining ishlarini belgilangan mezonlar asosida baholashi"
  },
  {
    question: "Innovatsion ta'limda **'Interfaol muhit'** nima?",
    options: [
      "Faqat qora doska",
      "O'quvchilarning bir-biri bilan, o'qituvchi va kontent bilan faol aloqada bo'lishi mumkin bo'lgan ta'lim sharoiti",
      "Faqat o'qituvchi gapiradi",
      "Faqat yozma ish"
    ],
    correctAnswer: "O'quvchilarning bir-biri bilan, o'qituvchi va kontent bilan faol aloqada bo'lishi mumkin bo'lgan ta'lim sharoiti"
  },
  {
    question: "Pedagogik texnologiyaning **'Obyektivlik'** prinsipi nima?",
    options: [
      "Faqat o'qituvchi xohishi",
      "Ta'lim natijalarini shaxsiy fikr yoki subyektivlikdan xoli, aniq mezonlar va standartlar asosida baholash",
      "Faqat qiyin vazifa",
      "Faqat oson vazifa"
    ],
    correctAnswer: "Ta'lim natijalarini shaxsiy fikr yoki subyektivlikdan xoli, aniq mezonlar va standartlar asosida baholash"
  },
  {
    question: "Ta'limda **'Refleksiya ko'nikmasi'** nima uchun rivojlantiriladi?",
    options: [
      "Faqat jazolash",
      "O'quvchida o'z xatti-harakatlari, fikrlari va ta'lim jarayonining sabab-natijalarini chuqur anglash qobiliyatini shakllantirish",
      "Faqat ma'ruza o'qish",
      "Faqat test yechish"
    ],
    correctAnswer: "O'quvchida o'z xatti-harakatlari, fikrlari va ta'lim jarayonining sabab-natijalarini chuqur anglash qobiliyatini shakllantirish"
  },
  {
    question: "Innovatsion ta'limda **'O'qitishning ijtimoiy jihati'** nima?",
    options: [
      "Faqat darslik",
      "Guruhda ishlash, muloqot, hamkorlik, bir-biridan o'rganish va ijtimoiy ko'nikmalarni rivojlantirish",
      "Faqat yakka ishlash",
      "Faqat ma'ruza"
    ],
    correctAnswer: "Guruhda ishlash, muloqot, hamkorlik, bir-biridan o'rganish va ijtimoiy ko'nikmalarni rivojlantirish"
  },
  {
    question: "AKT yordamida **'Onlayn kutubxonalar'**ning afzalligi nima?",
    options: [
      "Faqat qog'oz",
      "Katta hajmdagi axborotga istalgan joydan kirish, tezkor izlash va manbalarni yangilash imkoniyati",
      "Faqat musiqa",
      "Faqat rasm chizish"
    ],
    correctAnswer: "Katta hajmdagi axborotga istalgan joydan kirish, tezkor izlash va manbalarni yangilash imkoniyati"
  },
  {
    question: "Ta'limda **'Empatik tinglash'** nima?",
    options: [
      "Faqat eshitish",
      "Suhbatdoshning (o'quvchining) so'zlarini shunchaki eshitmasdan, uning his-tuyg'ularini va aytilganlarning ma'nosini tushunishga harakat qilish",
      "Faqat ma'ruza",
      "Faqat yozish"
    ],
    correctAnswer: "Suhbatdoshning (o'quvchining) so'zlarini shunchaki eshitmasdan, uning his-tuyg'ularini va aytilganlarning ma'nosini tushunishga harakat qilish"
  },
  {
    question: "Innovatsion ta'limda **'Ta'lim mazmuni'** qanday bo'lishi kerak?",
    options: [
      "Faqat eski",
      "Ilmiy jihatdan asoslangan, zamonaviy talablarga javob beradigan, amaliyotga yo'naltirilgan va o'zlashtirishga qulay",
      "Faqat qiyin",
      "Faqat yodlashga mo'ljallangan"
    ],
    correctAnswer: "Ilmiy jihatdan asoslangan, zamonaviy talablarga javob beradigan, amaliyotga yo'naltirilgan va o'zlashtirishga qulay"
  },
  {
    question: "Pedagogik texnologiyaning **'Reproduktiv'** o'qitish usuli nima?",
    options: [
      "Faqat yangi bilim yaratish",
      "O'quvchining tayyor ma'lumotni eslab qolishi va uni o'zgartirmasdan takrorlashi",
      "Faqat muammo yechish",
      "Faqat tadqiqot"
    ],
    correctAnswer: "O'quvchining tayyor ma'lumotni eslab qolishi va uni o'zgartirmasdan takrorlashi"
  },
  {
    question: "Ta'limda **'Muammoli topshiriq'** nima?",
    options: [
      "Faqat oddiy savol",
      "O'quvchidan oldingi bilimlarini qayta ishlab, yangi yechim yoki xulosa talab qiladigan, javobi tayyor bo'lmagan vaziyat",
      "Faqat yozish",
      "Faqat test"
    ],
    correctAnswer: "O'quvchidan oldingi bilimlarini qayta ishlab, yangi yechim yoki xulosa talab qiladigan, javobi tayyor bo'lmagan vaziyat"
  },
  {
    question: "Innovatsion ta'limda **'Ta'limning insonparvarlashuvi'** nima?",
    options: [
      "Faqat jazolash",
      "O'quvchining shaxsiga, uning ehtiyojlari, qiziqishlari va qobiliyatlariga e'tibor berish, hurmat qilish va rivojlanishiga yordam berish",
      "Faqat ma'ruza",
      "Faqat test"
    ],
    correctAnswer: "O'quvchining shaxsiga, uning ehtiyojlari, qiziqishlari va qobiliyatlariga e'tibor berish, hurmat qilish va rivojlanishiga yordam berish"
  },
  {
    question: "AKT yordamida **'Videoleksiya'**ning afzalligi nima?",
    options: [
      "Faqat musiqa",
      "Ma'ruzani istalgan vaqtda ko'rish, kerakli joyini takrorlash va vizual materiallar bilan boyitish imkoniyati",
      "Faqat rasm chizish",
      "Faqat yozish"
    ],
    correctAnswer: "Ma'ruzani istalgan vaqtda ko'rish, kerakli joyini takrorlash va vizual materiallar bilan boyitish imkoniyati"
  },
  {
    question: "Ta'limda **'Bilim ko'nikmasiga ega bo'lish'** nima?",
    options: [
      "Faqat yodlash",
      "O'rganilgan nazariy bilimlarni amaliy vaziyatlarda qo'llay olish",
      "Faqat ma'ruza",
      "Faqat baho"
    ],
    correctAnswer: "O'rganilgan nazariy bilimlarni amaliy vaziyatlarda qo'llay olish"
  },
  {
    question: "Innovatsion ta'limda **'Muammoga yo'naltirilgan ta'lim (PBL)'** nima?",
    options: [
      "Faqat ma'ruza",
      "O'quvchilarga avval muammoni berish va bilimni uni yechish jarayonida o'zlari mustaqil egallashini ta'minlash",
      "Faqat test yechish",
      "Faqat yozish"
    ],
    correctAnswer: "O'quvchilarga avval muammoni berish va bilimni uni yechish jarayonida o'zlari mustaqil egallashini ta'minlash"
  },
  {
    question: "Pedagogik texnologiyaning **'Integratsiya'** prinsipi nima?",
    options: [
      "Faqat bo'lish",
      "Ta'limning turli sohalari, fanlar, metodlar va texnologiyalarini o'zaro birlashtirish",
      "Faqat ajratish",
      "Faqat darslik"
    ],
    correctAnswer: "Ta'limning turli sohalari, fanlar, metodlar va texnologiyalarini o'zaro birlashtirish"
  },
  {
    question: "Ta'limda **'Kompyuterli testlash'**ning obyektivligi qanday ta'minlanadi?",
    options: [
      "Faqat o'qituvchi xohishi",
      "Baholashning oldindan belgilangan aniq algoritmlar asosida, inson omilisiz amalga oshirilishi",
      "Faqat yozma ish",
      "Faqat og'zaki javob"
    ],
    correctAnswer: "Baholashning oldindan belgilangan aniq algoritmlar asosida, inson omilisiz amalga oshirilishi"
  },
  {
    question: "Innovatsion ta'limda **'Ijodiy muhit'** nima?",
    options: [
      "Faqat qoidalar",
      "O'quvchilarning yangi g'oyalar, savollar va xavf-xatarlardan qo'rqmasdan erkin fikrlash, o'rganish va tajriba o'tkazishga undaydigan sharoit",
      "Faqat ma'ruza",
      "Faqat jazolash"
    ],
    correctAnswer: "O'quvchilarning yangi g'oyalar, savollar va xavf-xatarlardan qo'rqmasdan erkin fikrlash, o'rganish va tajriba o'tkazishga undaydigan sharoit"
  },
  {
    question: "AKT yordamida **'Shaxsiylashtirilgan ta'lim'**ni amalga oshirish qanday ta'minlanadi?",
    options: [
      "Faqat bir xil dars",
      "Adaptiv ta'lim tizimlari, o'quv faoliyatini tahlil qilish (Learning Analytics) va individual o'quv rejalari",
      "Faqat ma'ruza",
      "Faqat test"
    ],
    correctAnswer: "Adaptiv ta'lim tizimlari, o'quv faoliyatini tahlil qilish (Learning Analytics) va individual o'quv rejalari"
  },
  {
    question: "Ta'limda **'O'qituvchi-motivator'**ning roli nima?",
    options: [
      "Faqat jazolash",
      "O'quvchilarni o'rganishga rag'batlantirish, ularga o'ziga ishonch bag'ishlash va qiziqish uyg'otish",
      "Faqat baho qo'yish",
      "Faqat yozish"
    ],
    correctAnswer: "O'quvchilarni o'rganishga rag'batlantirish, ularga o'ziga ishonch bag'ishlash va qiziqish uyg'otish"
  },
  {
    question: "Innovatsion ta'limda **'O'quv jarayonining natijasi'**ga nimalar kiradi?",
    options: [
      "Faqat baho",
      "O'quvchining bilim, ko'nikma, malakasi, kompetentligi va shaxsiy rivojlanishi",
      "Faqat test natijasi",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "O'quvchining bilim, ko'nikma, malakasi, kompetentligi va shaxsiy rivojlanishi"
  },
  {
    question: "Pedagogik texnologiyaning **'Tizimlilik'** prinsipi nima?",
    options: [
      "Faqat tasodif",
      "Ta'lim maqsadlari, mazmuni, metodlari va natijalarining o'zaro bog'liq holda bir butun tizimni tashkil etishi",
      "Faqat chalkashlik",
      "Faqat yodlash"
    ],
    correctAnswer: "Ta'lim maqsadlari, mazmuni, metodlari va natijalarining o'zaro bog'liq holda bir butun tizimni tashkil etishi"
  },
  {
    question: "Psixika deganda nimani tushunasiz?",
    options: [
      "Faqat tana harakatlari",
      "Miyaning olamni aks ettiruvchi, borliqqa nisbatan faol munosabatini ifodalovchi xususiyati",
      "Faqat xotira",
      "Faqat tashqi muhit"
    ],
    correctAnswer: "Miyaning olamni aks ettiruvchi, borliqqa nisbatan faol munosabatini ifodalovchi xususiyati"
  },
  {
    question: "Psixologiya fanining asosiy predmeti nima?",
    options: [
      "Faqat insonning tanasi",
      "Inson va hayvonlarning psixikasi, psixik faoliyatining qonuniyatlari",
      "Faqat darsliklar",
      "Faqat tabiiy hodisalar"
    ],
    correctAnswer: "Inson va hayvonlarning psixikasi, psixik faoliyatining qonuniyatlari"
  },
  {
    question: "Psixik hodisalar tarkibiga kiruvchi **shaxsning individual ruhiy xususiyatlari** qaysi qatorda koërsatilgan?",
    options: [
      "Sezgi, idrok, xotira, tafakkur",
      "Temperament, xarakter, qobiliyat",
      "Hissiyot, iroda",
      "Diqqat, nutq, faoliyat"
    ],
    correctAnswer: "Temperament, xarakter, qobiliyat"
  },
  {
    question: "Diqqatning asosiy funksiyasi nima?",
    options: [
      "Faqat eslab qolish",
      "Shaxsning ongini maílum obyektga yoënaltirish va uzoq vaqt davomida barqaror qaratib tura olish",
      "Faqat gapirish",
      "Faqat yurish"
    ],
    correctAnswer: "Shaxsning ongini maílum obyektga yoënaltirish va uzoq vaqt davomida barqaror qaratib tura olish"
  },
  {
    question: "Diqqatning **'kontsentratsiyasi'** nima?",
    options: [
      "Faqat joyni o'zgartirish",
      "Insonning oëz diqqatini maílum obyektga uzoq vaqt davomida barqaror qaratib tura olishi",
      "Faqat eslab qolish tezligi",
      "Faqat yozish"
    ],
    correctAnswer: "Insonning oëz diqqatini maílum obyektga uzoq vaqt davomida barqaror qaratib tura olishi"
  },
  {
    question: "**Sezgi** qanday psixik jarayon?",
    options: [
      "Faqat fikrlash",
      "Tashqi va ichki muhitdagi alohida xususiyatlarning (rang, hid, harorat) bevosita miyada aks etishi",
      "Faqat xayol",
      "Faqat harakat"
    ],
    correctAnswer: "Tashqi va ichki muhitdagi alohida xususiyatlarning (rang, hid, harorat) bevosita miyada aks etishi"
  },
  {
    question: "**Idrok** (Vospriyatiye) nima?",
    options: [
      "Faqat bir xususiyatni aks ettirish",
      "Obíektlarni (narsalarni) butun holda, uning barcha xususiyatlari majmuida aks ettirish",
      "Faqat yozish",
      "Faqat xotira"
    ],
    correctAnswer: "Obíektlarni (narsalarni) butun holda, uning barcha xususiyatlari majmuida aks ettirish"
  },
  {
    question: "**Tafakkur**ning asosiy funksiyasi?",
    options: [
      "Faqat sezish",
      "Borliqning shaxsga bevosita berilmagan tomonlarini umumlashtirish va bilvosita (tushuncha, mulohaza, xulosa orqali) aks ettirish",
      "Faqat ko'rish",
      "Faqat eslab qolish"
    ],
    correctAnswer: "Borliqning shaxsga bevosita berilmagan tomonlarini umumlashtirish va bilvosita (tushuncha, mulohaza, xulosa orqali) aks ettirish"
  },
  {
    question: "**Xotira**ning asosiy jarayonlari qaysilar?",
    options: [
      "Faqat gapirish",
      "Eslab qolish (saqlash), esda saqlash, esga tushirish (tanib olish va qayta tiklash)",
      "Faqat harakat",
      "Faqat ko'rish"
    ],
    correctAnswer: "Eslab qolish (saqlash), esda saqlash, esga tushirish (tanib olish va qayta tiklash)"
  },
  {
    question: "Xayol (Fantaziya) qanday psixik jarayon?",
    options: [
      "Faqat yodlash",
      "Yangi obrazlar, tasavvurlar va g'oyalarni yaratishga qaratilgan aqliy jarayon",
      "Faqat jazolash",
      "Faqat tana harakati"
    ],
    correctAnswer: "Yangi obrazlar, tasavvurlar va g'oyalarni yaratishga qaratilgan aqliy jarayon"
  },
  {
    question: "Tafakkur turlari qaysi qatorda to'g'ri ko'rsatilgan?",
    options: [
      "Faqat ko'rgazmali",
      "Ko'rgazmali-harakatli, ko'rgazmali-obrazli, so'z-mantiqiy",
      "Faqat eslab qolish",
      "Faqat sezish"
    ],
    correctAnswer: "Ko'rgazmali-harakatli, ko'rgazmali-obrazli, so'z-mantiqiy"
  },
  {
    question: "**Temperament** nima?",
    options: [
      "Faqat bilim",
      "Shaxsning psixik faoliyatining dinamik tomonini (tezligi, kuchi, ritmi) belgilovchi tug'ma xususiyati",
      "Faqat xarakter",
      "Faqat qobiliyat"
    ],
    correctAnswer: "Shaxsning psixik faoliyatining dinamik tomonini (tezligi, kuchi, ritmi) belgilovchi tug'ma xususiyati"
  },
  {
    question: "Galen bo'yicha **temperamentning asosiy turlari** qaysilar?",
    options: [
      "Faqat tez va sekin",
      "Xolerik, Sangvinik, Flegmatik, Melanxolik",
      "Faqat quvnoq va xafa",
      "Faqat kuchli va kuchsiz"
    ],
    correctAnswer: "Xolerik, Sangvinik, Flegmatik, Melanxolik"
  },
  {
    question: "**Xarakter** nima?",
    options: [
      "Faqat tug'ma",
      "Shaxsning ijtimoiy munosabatlarda shakllanadigan, uning xatti-harakatlarida namoyon bo'ladigan barqaror individual xususiyatlari majmui",
      "Faqat eslab qolish",
      "Faqat sezish"
    ],
    correctAnswer: "Shaxsning ijtimoiy munosabatlarda shakllanadigan, uning xatti-harakatlarida namoyon bo'ladigan barqaror individual xususiyatlari majmui"
  },
  {
    question: "**Qobiliyat** nima?",
    options: [
      "Faqat harakat",
      "Muayyan faoliyatni muvaffaqiyatli bajarish uchun zarur bo'lgan individual-psixologik xususiyatlar",
      "Faqat xarakter",
      "Faqat temperament"
    ],
    correctAnswer: "Muayyan faoliyatni muvaffaqiyatli bajarish uchun zarur bo'lgan individual-psixologik xususiyatlar"
  },
  {
    question: "Qobiliyatning eng yuqori darajasi nima?",
    options: [
      "Ko'nikma",
      "Iste'dod (Talant) va zakovat (Aql-idrok)",
      "Malaka",
      "Xotira"
    ],
    correctAnswer: "Iste'dod (Talant) va zakovat (Aql-idrok)"
  },
  {
    question: "Psixik hodisalar tarkibiga kiruvchi **psixik holatlar** qaysilar?",
    options: [
      "Temperament, xarakter",
      "Eslab qolish, unutish",
      "Hissiyot, stress, kayfiyat, ishtiyoq (affekt)",
      "Nutq, faoliyat"
    ],
    correctAnswer: "Hissiyot, stress, kayfiyat, ishtiyoq (affekt)"
  },
  {
    question: "Hissiyot (Emotsiya) nima?",
    options: [
      "Faqat fikrlash",
      "Borliq hodisalariga nisbatan shaxsning subyektiv (ichki) baholovchi munosabatini ifodalovchi psixik jarayon",
      "Faqat yurish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Borliq hodisalariga nisbatan shaxsning subyektiv (ichki) baholovchi munosabatini ifodalovchi psixik jarayon"
  },
  {
    question: "**Affekt** (Ishtiyoq) qanday hissiy holat?",
    options: [
      "Uzoq davom etadigan, sust kayfiyat",
      "Qisqa muddatli, kuchli, shiddatli va keskin bo'ladigan hissiy portlash holati",
      "Faqat xotira",
      "Faqat fikr"
    ],
    correctAnswer: "Qisqa muddatli, kuchli, shiddatli va keskin bo'ladigan hissiy portlash holati"
  },
  {
    question: "Iroda (Volya) nima?",
    options: [
      "Faqat orzu",
      "Shaxsning oëz xatti-harakatlari, fikrlari va hissiyotlarini ongli ravishda boshqarish qobiliyati",
      "Faqat tana kuchi",
      "Faqat temperament"
    ],
    correctAnswer: "Shaxsning oëz xatti-harakatlari, fikrlari va hissiyotlarini ongli ravishda boshqarish qobiliyati"
  },
  {
    question: "Irodaviy harakatning asosiy bosqichlari?",
    options: [
      "Faqat harakat",
      "Maqsadni belgilash, harakat sabablarini kurashishi, qaror qabul qilish, uni amalga oshirish",
      "Faqat gapirish",
      "Faqat o'ylash"
    ],
    correctAnswer: "Maqsadni belgilash, harakat sabablarini kurashishi, qaror qabul qilish, uni amalga oshirish"
  },
  {
    question: "O'ziga bo'lgan **munosabatni ifodalovchi sifatlar** qaysi qatorda koërsatilgan?",
    options: [
      "Yaxshilik, mehribonlik",
      "Gëururlilik, shuhratparastlik, magërurlik, oëzini ulugëlash, kamtarlik",
      "Mehnatsevarlik, dangasalik",
      "Tozalik yoki ifloslik"
    ],
    correctAnswer: "Gëururlilik, shuhratparastlik, magërurlik, oëzini ulugëlash, kamtarlik"
  },
  {
    question: "**Interes (Qiziqish)** qanday psixik hodisa?",
    options: [
      "Faqat zerikish",
      "Shaxsning ma'lum faoliyatga, bilim olishga yo'nalganligi va uning ahamiyatini anglash",
      "Faqat tashqi muhit",
      "Faqat ovqatlanish"
    ],
    correctAnswer: "Shaxsning ma'lum faoliyatga, bilim olishga yo'nalganligi va uning ahamiyatini anglash"
  },
  {
    question: "**Ehtiyoj (Nujda)** nima?",
    options: [
      "Faqat xohish",
      "Shaxsning yashashi va rivojlanishi uchun zarur bo'lgan narsalar yetishmasligini anglash holati, faoliyatning manbai",
      "Faqat bilim",
      "Faqat temperament"
    ],
    correctAnswer: "Shaxsning yashashi va rivojlanishi uchun zarur bo'lgan narsalar yetishmasligini anglash holati, faoliyatning manbai"
  },
  {
    question: "A. Maslou bo'yicha ehtiyojlar piramidasining **eng quyi pog'onasi** nima?",
    options: [
      "Boshqalarni hurmat qilish ehtiyoji",
      "Fiziologik ehtiyojlar (ovqat, uyqu, nafas olish)",
      "Xavfsizlik ehtiyoji",
      "O'zini namoyon qilish ehtiyoji"
    ],
    correctAnswer: "Fiziologik ehtiyojlar (ovqat, uyqu, nafas olish)"
  },
  {
    question: "**Shaxs** (Lichnost) nima?",
    options: [
      "Faqat tug'ma xususiyatlar",
      "Ijtimoiy munosabatlar jarayonida shakllangan, o'ziga xos ongga ega bo'lgan subyekt",
      "Faqat tana",
      "Faqat miya"
    ],
    correctAnswer: "Ijtimoiy munosabatlar jarayonida shakllangan, o'ziga xos ongga ega bo'lgan subyekt"
  },
  {
    question: "**Individ** (Individual) tushunchasi nimani anglatadi?",
    options: [
      "Faqat ijtimoiy xususiyatlar",
      "Inson turining alohida vakili, uning tug'ma, biologik xususiyatlari majmui",
      "Faqat xarakter",
      "Faqat bilim"
    ],
    correctAnswer: "Inson turining alohida vakili, uning tug'ma, biologik xususiyatlari majmui"
  },
  {
    question: "**Individual yondashuv** (Psixologiyada) nimani anglatadi?",
    options: [
      "Faqat guruh bilan ishlash",
      "Ta'lim-tarbiya jarayonida har bir o'quvchining individual-psixologik xususiyatlarini (temperament, xarakter, qobiliyat) hisobga olish",
      "Faqat bir xil dars berish",
      "Faqat baho qo'yish"
    ],
    correctAnswer: "Ta'lim-tarbiya jarayonida har bir o'quvchining individual-psixologik xususiyatlarini (temperament, xarakter, qobiliyat) hisobga olish"
  },
  {
    question: "**Intellekt** (Aql-idrok) nima?",
    options: [
      "Faqat xotira",
      "Yangi sharoitga moslasha olish, bilim olish, muammolarni yechish va mavhum fikrlash qobiliyati",
      "Faqat jismoniy kuch",
      "Faqat temperament"
    ],
    correctAnswer: "Yangi sharoitga moslasha olish, bilim olish, muammolarni yechish va mavhum fikrlash qobiliyati"
  },
  {
    question: "Psixologiyada **faoliyat** nima?",
    options: [
      "Faqat yurish",
      "Shaxsning ehtiyojlarini qondirishga, maqsadga erishishga qaratilgan harakatlari majmui",
      "Faqat yozish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Shaxsning ehtiyojlarini qondirishga, maqsadga erishishga qaratilgan harakatlari majmui"
  },
  {
    question: "Faoliyatning asosiy turlari qaysilar?",
    options: [
      "Faqat o'ynash",
      "O'yin, o'qish (o'rganish), mehnat",
      "Faqat yozish, gapirish",
      "Faqat ko'rish, eshitish"
    ],
    correctAnswer: "O'yin, o'qish (o'rganish), mehnat"
  },
  {
    question: "Shaxsning **motivatsiyasi** nima?",
    options: [
      "Faqat qoidalar",
      "Shaxsni faoliyatga undaydigan, uning maqsad va ehtiyojlari bilan bog'liq bo'lgan ichki kuchlar tizimi",
      "Faqat temperament",
      "Faqat malaka"
    ],
    correctAnswer: "Shaxsni faoliyatga undaydigan, uning maqsad va ehtiyojlari bilan bog'liq bo'lgan ichki kuchlar tizimi"
  },
  {
    question: "**Krizis (Inqiroz)** yosh davrlari psixologiyasida nimani anglatadi?",
    options: [
      "Faqat kasallik",
      "Bolaning psixik rivojlanishida yangi sifat bosqichiga o'tish bilan bog'liq bo'lgan qisqa, keskin o'zgarishlar davri",
      "Faqat dam olish",
      "Faqat o'ynash"
    ],
    correctAnswer: "Bolaning psixik rivojlanishida yangi sifat bosqichiga o'tish bilan bog'liq bo'lgan qisqa, keskin o'zgarishlar davri"
  },
  {
    question: "**O'smirlik davri**ning (11-15 yosh) psixologik xususiyatlari?",
    options: [
      "Faqat o'yin",
      "Tana o'zgarishlari, o'zlikni anglashning kuchayishi, yetakchilikka intilish, mustaqillikka ehtiyoj",
      "Faqat ota-onaga bo'ysunish",
      "Faqat maktabga borish"
    ],
    correctAnswer: "Tana o'zgarishlari, o'zlikni anglashning kuchayishi, yetakchilikka intilish, mustaqillikka ehtiyoj"
  },
  {
    question: "Bolaning rivojlanishida **o'yin faoliyati**ning asosiy o'rni nima?",
    options: [
      "Faqat vaqt o'tkazish",
      "Ijtimoiy munosabatlarni, muloqotni, irodani va rolli xatti-harakatlarni o'rganish",
      "Faqat ovqatlanish",
      "Faqat yozish"
    ],
    correctAnswer: "Ijtimoiy munosabatlarni, muloqotni, irodani va rolli xatti-harakatlarni o'rganish"
  },
  {
    question: "**Kommunikatsiya** (Muloqot) nima?",
    options: [
      "Faqat fikrlash",
      "Odamlar o'rtasida axborot, tajriba, bilim va hissiyotlarni almashish jarayoni",
      "Faqat yurish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Odamlar o'rtasida axborot, tajriba, bilim va hissiyotlarni almashish jarayoni"
  },
  {
    question: "Muloqotning **verbal** (og'zaki) vositalariga nimalar kiradi?",
    options: [
      "Mimika, jestlar",
      "Nutq, so'z, ovoz ohangi",
      "Kiyim, soch turmagi",
      "Yurish usuli"
    ],
    correctAnswer: "Nutq, so'z, ovoz ohangi"
  },
  {
    question: "Muloqotning **noverbal** (og'zaki bo'lmagan) vositalariga nimalar kiradi?",
    options: [
      "So'zlar, jumlalar",
      "Mimika, jestlar, pantomimika, intonatsiya, nigoh",
      "Ma'ruza",
      "Kitoblar"
    ],
    correctAnswer: "Mimika, jestlar, pantomimika, intonatsiya, nigoh"
  },
  {
    question: "**Stress** qanday psixik holat?",
    options: [
      "Faqat dam olish",
      "Organizmning juda kuchli ta'sirga (xavf, xursandlik, jismoniy zo'riqish) javoban beradigan umumiy javobi (ruhiy va fiziologik keskinlik)",
      "Faqat o'ynash",
      "Faqat uxlash"
    ],
    correctAnswer: "Organizmning juda kuchli ta'sirga (xavf, xursandlik, jismoniy zo'riqish) javoban beradigan umumiy javobi (ruhiy va fiziologik keskinlik)"
  },
  {
    question: "**Konflikt (Ziddiyat)** nima?",
    options: [
      "Faqat do'stlik",
      "Odamlar, guruhlar yoki ichki shaxsiy motivlar o'rtasidagi qarama-qarshi maqsadlar, manfaatlar yoki pozitsiyalar to'qnashuvi",
      "Faqat hamkorlik",
      "Faqat yordam"
    ],
    correctAnswer: "Odamlar, guruhlar yoki ichki shaxsiy motivlar o'rtasidagi qarama-qarshi maqsadlar, manfaatlar yoki pozitsiyalar to'qnashuvi"
  },
  {
    question: "Psixologiyada **'Bilimlar (Kognitiv) jarayonlar'** nimalar?",
    options: [
      "Faqat hissiyot",
      "Sezgi, idrok, xotira, tafakkur, xayol va diqqat",
      "Faqat xarakter",
      "Faqat iroda"
    ],
    correctAnswer: "Sezgi, idrok, xotira, tafakkur, xayol va diqqat"
  },
  {
    question: "**Eidetik xotira** nima?",
    options: [
      "Faqat ovozli xotira",
      "Ob'ektni go'yo uni hali ham ko'rayotgandek, juda aniq va to'liq eslab qolish qobiliyati (fotografik xotira)",
      "Faqat harakat xotirasi",
      "Faqat hissiyot xotirasi"
    ],
    correctAnswer: "Ob'ektni go'yo uni hali ham ko'rayotgandek, juda aniq va to'liq eslab qolish qobiliyati (fotografik xotira)"
  },
  {
    question: "**Analiz (Tahlil)** va **Sintez** (Tafakkurda) nima?",
    options: [
      "Faqat bir jarayon",
      "Analiz - butunni qismlarga ajratish, Sintez - qismlardan butunni yaratish",
      "Faqat eslab qolish",
      "Faqat ko'rish"
    ],
    correctAnswer: "Analiz - butunni qismlarga ajratish, Sintez - qismlardan butunni yaratish"
  },
  {
    question: "**Kreativlik** (Ijodkorlik) nima?",
    options: [
      "Faqat qoidalar bo'yicha ishlash",
      "Yangi va noyob g'oyalar, yechimlar yoki mahsulotlar yaratish qobiliyati",
      "Faqat eslab qolish",
      "Faqat jazolash"
    ],
    correctAnswer: "Yangi va noyob g'oyalar, yechimlar yoki mahsulotlar yaratish qobiliyati"
  },
  {
    question: "**Mijozlarga yo'naltirilgan terapiya** (K. Rodjers) nimani anglatadi?",
    options: [
      "Faqat maslahat berish",
      "Terapistning mijozni qabul qilishi, unga hamdardlik (empatiya) bildirish va uni qo'llab-quvvatlash",
      "Faqat jazolash",
      "Faqat buyruq berish"
    ],
    correctAnswer: "Terapistning mijozni qabul qilishi, unga hamdardlik (empatiya) bildirish va uni qo'llab-quvvatlash"
  },
  {
    question: "A. Maslou bo'yicha ehtiyojlar piramidasining **eng yuqori pog'onasi** nima?",
    options: [
      "Fiziologik ehtiyojlar",
      "Xavfsizlik ehtiyoji",
      "O'zini namoyon qilish (aktualizatsiya) ehtiyoji",
      "Muloqot ehtiyoji"
    ],
    correctAnswer: "O'zini namoyon qilish (aktualizatsiya) ehtiyoji"
  },
  {
    question: "**Neyropsixologiya** nima?",
    options: [
      "Faqat hayvonlar psixologiyasi",
      "Miya tuzilishi va uning alohida qismlari bilan psixik jarayonlar o'rtasidagi bog'liqlikni o'rganadigan fan",
      "Faqat ijtimoiy psixologiya",
      "Faqat kasb psixologiyasi"
    ],
    correctAnswer: "Miya tuzilishi va uning alohida qismlari bilan psixik jarayonlar o'rtasidagi bog'liqlikni o'rganadigan fan"
  },
  {
    question: "**Persepsiya** tushunchasi psixologiyada nimani bildiradi?",
    options: [
      "Sezgi",
      "Idrok",
      "Xotira",
      "Diqqat"
    ],
    correctAnswer: "Idrok"
  },
  {
    question: "**Flegmatik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Haddan tashqari shoshqaloqlik va beqarorlik",
      "Sokin, sust, hissiyotlarni kam namoyon etadigan, sekin, ammo barqaror",
      "Haddan tashqari optimist, serharakat",
      "Haddan tashqari xafa, tushkun"
    ],
    correctAnswer: "Sokin, sust, hissiyotlarni kam namoyon etadigan, sekin, ammo barqaror"
  },
  {
    question: "**Melanxolik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Serharakat, doimo o'zgaruvchan",
      "Juda ta'sirchan, tez charchaydigan, yengil tushkunlikka tushuvchi, sust, o'ziga ishonchsiz",
      "Kuchli, tezkor, hissiyotlarga beriluvchan",
      "Sokin, harakatsiz, deyarli hissiyotsiz"
    ],
    correctAnswer: "Juda ta'sirchan, tez charchaydigan, yengil tushkunlikka tushuvchi, sust, o'ziga ishonchsiz"
  },
  {
    question: "**Holerik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Sokin, bosiq",
      "Kuchli, tezkor, muvozanatsiz, tezda jahli chiqadigan, hissiyotlarga beriluvchan",
      "Serharakat, quvnoq, barqaror",
      "Sust, xafa"
    ],
    correctAnswer: "Kuchli, tezkor, muvozanatsiz, tezda jahli chiqadigan, hissiyotlarga beriluvchan"
  },
  {
    question: "**Sangvinik** temperamentli odamning asosiy xususiyati?",
    options: [
      "Sokin, bosiq, sust",
      "Serharakat, quvnoq, optimist, tez moslashuvchan, hissiyotlari tez o'zgaruvchan",
      "Muvozanatsiz, jahlga tez beriluvchan",
      "Juda ta'sirchan, o'ziga ishonchsiz"
    ],
    correctAnswer: "Serharakat, quvnoq, optimist, tez moslashuvchan, hissiyotlari tez o'zgaruvchan"
  },
  {
    question: "**Appersepsiya** nima?",
    options: [
      "Faqat eslab qolish",
      "Idrokning shaxsning avvalgi tajribasi, bilimi va qiziqishlariga bog'liqligi",
      "Faqat sezish",
      "Faqat xayol"
    ],
    correctAnswer: "Idrokning shaxsning avvalgi tajribasi, bilimi va qiziqishlariga bog'liqligi"
  },
  {
    question: "**Qobiliyatning rivojlanish darajalari** qaysilar?",
    options: [
      "Bilim, ko'nikma",
      "Iste'dod (Talant), Zakovat (Aql-idrok), Geniallik",
      "Malaka, harakat",
      "Diqqat, xotira"
    ],
    correctAnswer: "Iste'dod (Talant), Zakovat (Aql-idrok), Geniallik"
  },
  {
    question: "**Muloqotning perseptiv tomoni** nima?",
    options: [
      "Faqat axborot almashish",
      "Suhbatdoshni (sherikni) idrok etish, uni tushunish va baholash jarayoni",
      "Faqat ta'sir o'tkazish",
      "Faqat so'zlashish"
    ],
    correctAnswer: "Suhbatdoshni (sherikni) idrok etish, uni tushunish va baholash jarayoni"
  },
  {
    question: "**Empatiya** (Psixologiyada) nima?",
    options: [
      "Faqat baholash",
      "Boshqa odamning hissiyotlarini, holatini ichki tomondan tushuna olish va hamdardlik bildirish qobiliyati",
      "Faqat jazolash",
      "Faqat o'ylash"
    ],
    correctAnswer: "Boshqa odamning hissiyotlarini, holatini ichki tomondan tushuna olish va hamdardlik bildirish qobiliyati"
  },
  {
    question: "**Refleksiya** (Psixologiyada) nima?",
    options: [
      "Faqat tashqariga qarash",
      "Shaxsning oëz ichki ruhiy holati, fikrlari, xatti-harakatlari va o'zgarishlarini o'zi tahlil qilishi",
      "Faqat yugurish",
      "Faqat tinglash"
    ],
    correctAnswer: "Shaxsning oëz ichki ruhiy holati, fikrlari, xatti-harakatlari va o'zgarishlarini o'zi tahlil qilishi"
  },
  {
    question: "**Diqqatning barqarorligi** nima?",
    options: [
      "Faqat tez o'tish",
      "Diqqatning ma'lum obyektdan chalg'imasdan, uzoq vaqt davomida saqlana olish qobiliyati",
      "Faqat tez charchash",
      "Faqat bo'linish"
    ],
    correctAnswer: "Diqqatning ma'lum obyektdan chalg'imasdan, uzoq vaqt davomida saqlana olish qobiliyati"
  },
  {
    question: "**O'qish faoliyati** (Psixologiyada) qanday faoliyat turi?",
    options: [
      "Faqat o'yin",
      "Nazariy bilimlar, ko'nikmalar va malakalarni o'zlashtirishga qaratilgan faoliyat",
      "Faqat mehnat",
      "Faqat dam olish"
    ],
    correctAnswer: "Nazariy bilimlar, ko'nikmalar va malakalarni o'zlashtirishga qaratilgan faoliyat"
  },
  {
    question: "Tafakkur jarayonida **generallashuv (umumlashtirish)** nima?",
    options: [
      "Faqat ajratish",
      "Ob'ektlar va hodisalarning muhim va umumiy xususiyatlarini ajratib olish va ularni tushuncha ostida birlashtirish",
      "Faqat taqqoslash",
      "Faqat analiz"
    ],
    correctAnswer: "Ob'ektlar va hodisalarning muhim va umumiy xususiyatlarini ajratib olish va ularni tushuncha ostida birlashtirish"
  },
  {
    question: "**Vizual xotira** nima?",
    options: [
      "Faqat eshitish orqali eslab qolish",
      "Ko'rish orqali idrok qilingan obrazlar va ma'lumotlarni eslab qolish va qayta tiklash",
      "Faqat harakat orqali eslab qolish",
      "Faqat hissiyot orqali eslab qolish"
    ],
    correctAnswer: "Ko'rish orqali idrok qilingan obrazlar va ma'lumotlarni eslab qolish va qayta tiklash"
  },
  {
    question: "**Ijtimoiy idrok** (Sotsialnaya persepsiya) nima?",
    options: [
      "Faqat narsalarni idrok etish",
      "Odamlarning bir-birini, o'zini, ijtimoiy ob'ektlar va guruhlarni idrok etish, tushunish va baholash jarayoni",
      "Faqat tovushni eshitish",
      "Faqat rangni ko'rish"
    ],
    correctAnswer: "Odamlarning bir-birini, o'zini, ijtimoiy ob'ektlar va guruhlarni idrok etish, tushunish va baholash jarayoni"
  },
  {
    question: "**Kattalar yoshidagi krizislar** (masalan, 30, 40 yosh) nima bilan bog'liq?",
    options: [
      "Faqat jismoniy o'zgarishlar",
      "Hayot mazmunini qayta baholash, maqsadlarni o'zgartirish, shaxsiy va professional o'zlikni izlash",
      "Faqat temperament o'zgarishi",
      "Faqat ovqatlanish"
    ],
    correctAnswer: "Hayot mazmunini qayta baholash, maqsadlarni o'zgartirish, shaxsiy va professional o'zlikni izlash"
  },
  {
    question: "**Shaxsning yo'nalganligi** (Napravlennost lichnosti) nima?",
    options: [
      "Faqat yugurish",
      "Ehtiyojlar, qiziqishlar, e'tiqodlar va ideallar tizimi orqali belgilanadigan, shaxsning faoliyatini boshqaruvchi motivlar majmui",
      "Faqat o'ylash",
      "Faqat harakat"
    ],
    correctAnswer: "Ehtiyojlar, qiziqishlar, e'tiqodlar va ideallar tizimi orqali belgilanadigan, shaxsning faoliyatini boshqaruvchi motivlar majmui"
  },
  {
    question: "**Kichik maktab yoshi** (6-11 yosh) uchun asosiy faoliyat turi?",
    options: [
      "O'yin",
      "O'qish (o'rganish)",
      "Mehnat",
      "Muloqot"
    ],
    correctAnswer: "O'qish (o'rganish)"
  },
  {
    question: "**Muloqotning interaktiv tomoni** nima?",
    options: [
      "Faqat tushunish",
      "Odamlarning bir-biriga ta'sir o'tkazishi, harakatlarni tashkil etish va hamkorlik qilish",
      "Faqat axborot almashish",
      "Faqat baholash"
    ],
    correctAnswer: "Odamlarning bir-biriga ta'sir o'tkazishi, harakatlarni tashkil etish va hamkorlik qilish"
  },
  {
    question: "**O'z-o'zini baholash (Samootsenka)** nima?",
    options: [
      "Faqat boshqalarning bahosi",
      "Shaxsning o'z qobiliyatlari, fazilatlari, yutuqlari va kamchiliklariga beradigan subyektiv bahosi",
      "Faqat maktab bahosi",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "Shaxsning o'z qobiliyatlari, fazilatlari, yutuqlari va kamchiliklariga beradigan subyektiv bahosi"
  },
  {
    question: "Maxsus pedagogika fani qanday fan?",
    options: [
      "Faqat sog'lom bolalar ta'limi bilan shug'ullanadigan fan",
      "Jismoniy va ruhiy rivojlanishda nuqsoni bo`lgan bolalar ta'lim tarbiyasi bilan shug'ullanadigan fan",
      "Faqat oliy ta'limni o'rganadigan fan",
      "Faqat ijtimoiy munosabatlarni o'rganadigan fan"
    ],
    correctAnswer: "Jismoniy va ruhiy rivojlanishda nuqsoni bo`lgan bolalar ta'lim tarbiyasi bilan shug'ullanadigan fan"
  },
  {
    question: "Maxsus pedagogika fanining asosiy vazifalaridan biri nima?",
    options: [
      "Faqat sog'lom bolalarni o'qitish",
      "Maxsus yordamga muxtoj bolalarning ijtimoiy adabtatsiya, reabilitatsiya, kompensatsiyasini amalga oshirish",
      "Faqat darslik yaratish",
      "Faqat sport bilan shug'ullanish"
    ],
    correctAnswer: "Maxsus yordamga muxtoj bolalarning ijtimoiy adabtatsiya, reabilitatsiya, kompensatsiyasini amalga oshirish"
  },
  {
    question: "Maxsus pedagogika fanining mustaqil tarmoqlari qaysilar?",
    options: [
      "Oligofrenopedagogika, oftalmologiya, dermotologiya, logopediya",
      "Surdopedagogika, stomatologiya, fiziologiya, patologiya",
      "Tiflopedagogika, ottorinoloringologiya, rinoplastika, surdologiya",
      "Logopediya, Surdopedagogika, Tiflopedagogika, Oligofrenopedagogika"
    ],
    correctAnswer: "Logopediya, Surdopedagogika, Tiflopedagogika, Oligofrenopedagogika"
  },
  {
    question: "**Surdopedagogika** qanday bolalar ta'limi bilan shug'ullanadi?",
    options: [
      "Ko'rishida nuqsoni bo'lgan bolalar",
      "Eshitishida nuqsoni bo'lgan bolalar (kar, zaif eshituvchi)",
      "Aqli zaif bolalar",
      "Nutqida nuqsoni bo'lgan bolalar"
    ],
    correctAnswer: "Eshitishida nuqsoni bo'lgan bolalar (kar, zaif eshituvchi)"
  },
  {
    question: "**Tiflopedagogika** qanday bolalar ta'limi bilan shug'ullanadi?",
    options: [
      "Eshitishida nuqsoni bo'lgan bolalar",
      "Ko'rishida nuqsoni bo'lgan bolalar (ko'r, zaif ko'ruvchi)",
      "Aqli zaif bolalar",
      "Nutqida nuqsoni bo'lgan bolalar"
    ],
    correctAnswer: "Ko'rishida nuqsoni bo'lgan bolalar (ko'r, zaif ko'ruvchi)"
  },
  {
    question: "**Oligofrenopedagogika** qanday bolalar ta'limi bilan shug'ullanadi?",
    options: [
      "Eshitishida nuqsoni bo'lgan bolalar",
      "Aqliy rivojlanishida nuqsoni (aqli zaif) bo'lgan bolalar",
      "Ko'rishida nuqsoni bo'lgan bolalar",
      "Nutqida nuqsoni bo'lgan bolalar"
    ],
    correctAnswer: "Aqliy rivojlanishida nuqsoni (aqli zaif) bo'lgan bolalar"
  },
  {
    question: "**Logopediya** fani nimani o'rganadi?",
    options: [
      "Eshitish nuqsonlarini",
      "Nutq nuqsonlarining sabablari, mexanizmlari, belgilari, oldini olish va tuzatish usullarini",
      "Ko'rish nuqsonlarini",
      "Tayanch-harakat a'zolari nuqsonlarini"
    ],
    correctAnswer: "Nutq nuqsonlarining sabablari, mexanizmlari, belgilari, oldini olish va tuzatish usullarini"
  },
  {
    question: "**Disleksiya** nutq nuqsoni nimada namoyon bo'ladi?",
    options: [
      "Yozuvda nuqson",
      "O'qish jarayonini buzilishi (o'qishdagi qiyinchilik)",
      "Nutq tovushlarini talaffuz qilishdagi nuqson",
      "Yozishdagi qiyinchilik"
    ],
    correctAnswer: "O'qish jarayonini buzilishi (o'qishdagi qiyinchilik)"
  },
  {
    question: "**Inklyuziv taílim** deganda nimani tushunasiz?",
    options: [
      "Faqat maxsus maktabda o'qitish",
      "Imkoniyati cheklangan bolalarning sogëlom tengdoshlari bilan birga umumiy taílim maktablarida oëqitilishi",
      "Faqat uyda o'qitish",
      "Faqat alohida o'qitish"
    ],
    correctAnswer: "Imkoniyati cheklangan bolalarning sogëlom tengdoshlari bilan birga umumiy taílim maktablarida oëqitilishi"
  },
  {
    question: "Inklyuziv taílimning asosiy maqsadi nima?",
    options: [
      "Faqat bolalarni ajratish",
      "Barcha bolalar uchun sifatli taílim olishga teng imkoniyat yaratish va ularning ijtimoiy integratsiyasini ta'minlash",
      "Faqat alohida dars berish",
      "Faqat ota-onalarni cheklash"
    ],
    correctAnswer: "Barcha bolalar uchun sifatli taílim olishga teng imkoniyat yaratish va ularning ijtimoiy integratsiyasini ta'minlash"
  },
  {
    question: "Inklyuziv taílimda **'individual yondashuv'** nimani anglatadi?",
    options: [
      "Barchani bir xil baholash",
      "Har bir bolaga uning individual imkoniyatiga, ehtiyojiga va qobiliyatiga mos topshiriq va sharoit berish",
      "Faqat oddiy darslikdan foydalanish",
      "Ajratilgan oëquv dasturi"
    ],
    correctAnswer: "Har bir bolaga uning individual imkoniyatiga, ehtiyojiga va qobiliyatiga mos topshiriq va sharoit berish"
  },
  {
    question: "Inklyuziv taílimning asosiy tamoyillaridan biri?",
    options: [
      "Faqat nazorat",
      "Hamkorlik va tenglik",
      "Ajratish",
      "Faqat maktab direktori qarori"
    ],
    correctAnswer: "Hamkorlik va tenglik"
  },
  {
    question: "Imkoniyati cheklangan bolalarni jalb qilishda qanday **texnologiyalar** muhim?",
    options: [
      "Oddiy daftar",
      "Moslashtirilgan kompyuter va texnik vositalar (yirik shriftli, sensorli, Braille displeylari)",
      "Telefon",
      "Qoëshni yordamida"
    ],
    correctAnswer: "Moslashtirilgan kompyuter va texnik vositalar (yirik shriftli, sensorli, Braille displeylari)"
  },
  {
    question: "Inklyuziv taílimda **'moslashtirilgan baholash'** nimani bildiradi?",
    options: [
      "Faqat imtihon natijasi",
      "Bolaning individual imkoniyatiga, uning o'quv dasturidagi o'zgarishlarga qarab baholash",
      "Oddiy standart baholash",
      "Faqat yozma topshiriqlar"
    ],
    correctAnswer: "Bolaning individual imkoniyatiga, uning o'quv dasturidagi o'zgarishlarga qarab baholash"
  },
  {
    question: "**Integratsiyalashgan taílim**da sogëlom bolalar uchun qanday afzallik bor?",
    options: [
      "Faqat bilim olish",
      "Mehr-shafqat, tolerantlik (bag'rikenglik) va boshqalar ehtiyojlarini tushunishni oërganish",
      "Faqat o'yin",
      "Faqat jismoniy rivojlanish"
    ],
    correctAnswer: "Mehr-shafqat, tolerantlik (bag'rikenglik) va boshqalar ehtiyojlarini tushunishni oërganish"
  },
  {
    question: "**Kompleks yondashuv** (maxsus pedagogikada) nima?",
    options: [
      "Faqat o'qituvchi",
      "Ta'lim-tarbiya, tibbiy yordam, psixologik qo'llab-quvvatlash va ijtimoiy yordamni birgalikda qo'llash",
      "Faqat ota-ona",
      "Faqat maktab"
    ],
    correctAnswer: "Ta'lim-tarbiya, tibbiy yordam, psixologik qo'llab-quvvatlash va ijtimoiy yordamni birgalikda qo'llash"
  },
  {
    question: "**Kompensatsiya** (maxsus pedagogikada) nima?",
    options: [
      "Faqat bilim berish",
      "Biror nuqson tufayli buzilgan funksiyalarni boshqa organlar yoki funksiyalar yordamida qoplash",
      "Faqat jazolash",
      "Faqat o'yin"
    ],
    correctAnswer: "Biror nuqson tufayli buzilgan funksiyalarni boshqa organlar yoki funksiyalar yordamida qoplash"
  },
  {
    question: "**Korreksiya** (Tuzatish) nimani anglatadi?",
    options: [
      "Faqat baholash",
      "Rivojlanishdagi nuqsonlarni bartaraf etish yoki yumshatishga qaratilgan pedagogik harakatlar",
      "Faqat ma'ruza",
      "Faqat o'yin"
    ],
    correctAnswer: "Rivojlanishdagi nuqsonlarni bartaraf etish yoki yumshatishga qaratilgan pedagogik harakatlar"
  },
  {
    question: "**Reabilitatsiya** (tiklash) nima?",
    options: [
      "Faqat jismoniy mashq",
      "Maxsus ehtiyojli shaxsning ijtimoiy hayotga, mehnatga va jamiyatga faol qatnashish qobiliyatini tiklash",
      "Faqat o'qish",
      "Faqat yozish"
    ],
    correctAnswer: "Maxsus ehtiyojli shaxsning ijtimoiy hayotga, mehnatga va jamiyatga faol qatnashish qobiliyatini tiklash"
  },
  {
    question: "**Braille alifbosi** qaysi turdagi nuqsoni bo'lgan bolalar uchun mo'ljallangan?",
    options: [
      "Eshitishida nuqsoni bo'lganlar",
      "Ko'rishida nuqsoni bo'lganlar (ko'rlar)",
      "Aqli zaiflar",
      "Nutqida nuqsoni bo'lganlar"
    ],
    correctAnswer: "Ko'rishida nuqsoni bo'lganlar (ko'rlar)"
  },
  {
    question: "**Daktilologiya** (barmoq alifbosi) kimlar bilan muloqot qilishda qo'llaniladi?",
    options: [
      "Ko'rlar",
      "Karlar (eshitmaydiganlar)",
      "Aqli zaiflar",
      "Tayanch-harakat a'zolari nuqsoni bo'lganlar"
    ],
    correctAnswer: "Karlar (eshitmaydiganlar)"
  },
  {
    question: "**Surdoguruxlar** (Maxsus maktablarda) qanday bolalar uchun tashkil etiladi?",
    options: [
      "Ko'rlar",
      "Eshitishida nuqsoni bo'lganlar",
      "Aqli zaiflar",
      "Nutqida nuqsoni bo'lganlar"
    ],
    correctAnswer: "Eshitishida nuqsoni bo'lganlar"
  },
  {
    question: "**Oligofreniya** (Aqli zaiflik) sabablari?",
    options: [
      "Faqat yomon darslik",
      "Irsiy omillar, homiladorlik davridagi patologiyalar, tug'ruqdagi shikastlanishlar, ilk yoshdagi kasalliklar",
      "Faqat noto'g'ri baho",
      "Faqat yomon o'qituvchi"
    ],
    correctAnswer: "Irsiy omillar, homiladorlik davridagi patologiyalar, tug'ruqdagi shikastlanishlar, ilk yoshdagi kasalliklar"
  },
  {
    question: "**Maxsus maktablar**ning maqsadi?",
    options: [
      "Faqat sog'lom bolalarni o'qitish",
      "Rivojlanishdagi nuqsonlarni inobatga olgan holda, chuqurlashtirilgan korreksion ta'lim-tarbiya berish",
      "Faqat kasb o'rgatish",
      "Faqat sport bilan shug'ullanish"
    ],
    correctAnswer: "Rivojlanishdagi nuqsonlarni inobatga olgan holda, chuqurlashtirilgan korreksion ta'lim-tarbiya berish"
  },
  {
    question: "**Nutq terapiyasi** (Logopediya) nima uchun kerak?",
    options: [
      "Faqat yugurish",
      "Nutq nuqsonlarini tuzatish, nutqni rivojlantirish va muloqot ko'nikmalarini yaxshilash",
      "Faqat rasm chizish",
      "Faqat uxlash"
    ],
    correctAnswer: "Nutq nuqsonlarini tuzatish, nutqni rivojlantirish va muloqot ko'nikmalarini yaxshilash"
  },
  {
    question: "Tiflopedagogikada o'qitishda **qolgan sezgi organlari**dan qanday foydalaniladi?",
    options: [
      "Faqat ko'rish",
      "Eshitish va sezish (tuyish, teri retseptorlari) sezgilarini rivojlantirish orqali kompensatsiya qilish",
      "Faqat hid bilish",
      "Faqat ta'm bilish"
    ],
    correctAnswer: "Eshitish va sezish (tuyish, teri retseptorlari) sezgilarini rivojlantirish orqali kompensatsiya qilish"
  },
  {
    question: "Maxsus pedagogikada **'Tashxis' (Diagnostika)** nimani anglatadi?",
    options: [
      "Faqat dars berish",
      "Bolaning rivojlanishdagi nuqson turi, darajasi va sabablarini aniqlash, korreksion ish rejasini tuzish",
      "Faqat baholash",
      "Faqat uy vazifasi"
    ],
    correctAnswer: "Bolaning rivojlanishdagi nuqson turi, darajasi va sabablarini aniqlash, korreksion ish rejasini tuzish"
  },
  {
    question: "Inklyuziv taílim muhitida **o'qituvchi-defektolog**ning o'rni?",
    options: [
      "Faqat oddiy dars o'tish",
      "Maxsus ehtiyojli bolalar uchun ta'lim jarayonini moslashtirish va korreksion yordam berish",
      "Faqat baho qo'yish",
      "Faqat sport mashg'ulotlari o'tish"
    ],
    correctAnswer: "Maxsus ehtiyojli bolalar uchun ta'lim jarayonini moslashtirish va korreksion yordam berish"
  },
  {
    question: "**Aqli zaif bolalar**ga o'rgatishning asosiy prinsipi nima?",
    options: [
      "Faqat murakkab nazariya",
      "Ko'rgazmalilik, amaliy faoliyatga yo'naltirish, materialni sekin, takrorlab va qismlarga bo'lib berish",
      "Faqat tez o'qitish",
      "Faqat yodlash"
    ],
    correctAnswer: "Ko'rgazmalilik, amaliy faoliyatga yo'naltirish, materialni sekin, takrorlab va qismlarga bo'lib berish"
  },
  {
    question: "**Disgrafiya** nutq nuqsoni qaysi jarayon bilan bog'liq?",
    options: [
      "O'qish jarayoni",
      "Nutqni talaffuz qilish",
      "Yozma nutqni buzilishi (yozishdagi xatolar, qiyinchilik)",
      "Eshitish"
    ],
    correctAnswer: "Yozma nutqni buzilishi (yozishdagi xatolar, qiyinchilik)"
  },
  {
    question: "**O'yin terapiyasi** qaysi maxsus ehtiyojli bolalar bilan ishlashda samarali?",
    options: [
      "Faqat ko'rlar",
      "Emotsional-irodaviy sohada buzilishi bor, autizm spektridagi yoki aqliy zaif bolalar",
      "Faqat karlar",
      "Faqat katta yoshlilar"
    ],
    correctAnswer: "Emotsional-irodaviy sohada buzilishi bor, autizm spektridagi yoki aqliy zaif bolalar"
  },
  {
    question: "**Maxsus ta'limning individual dasturi (IUP)** nima uchun kerak?",
    options: [
      "Faqat o'qituvchiga yukni kamaytirish",
      "Har bir maxsus ehtiyojli bolaning o'zlashtirish tezligi, maqsadlari va korreksion vazifalarini belgilash",
      "Faqat baho qo'yish",
      "Faqat sport bilan shug'ullanish"
    ],
    correctAnswer: "Har bir maxsus ehtiyojli bolaning o'zlashtirish tezligi, maqsadlari va korreksion vazifalarini belgilash"
  },
  {
    question: "**Imkoniyati cheklangan bolalarning ijtimoiy integratsiyasi** nimani anglatadi?",
    options: [
      "Faqat alohida yashash",
      "Ular jamiyatning teng huquqli a'zosi bo'lib, uning hayotida faol ishtirok etishlari",
      "Faqat uyda qolish",
      "Faqat maxsus maktabda o'qish"
    ],
    correctAnswer: "Ular jamiyatning teng huquqli a'zosi bo'lib, uning hayotida faol ishtirok etishlari"
  },
  {
    question: "**Surdopedagogikada nutqni rivojlantirish**ning asosiy usuli?",
    options: [
      "Faqat o'qish",
      "Og'zaki nutq, daktilologiya, imo-ishoralar tilini integrativ (birgalikda) qo'llash",
      "Faqat yozish",
      "Faqat rasm chizish"
    ],
    correctAnswer: "Og'zaki nutq, daktilologiya, imo-ishoralar tilini integrativ (birgalikda) qo'llash"
  },
  {
    question: "**Tiflopedagogikada orientatsiya va mobillik** nima?",
    options: [
      "Faqat turish",
      "Ko'r va zaif ko'ruvchi bolalarga atrof muhitda mustaqil harakat qilishni o'rgatish (oq tayoq, eshitish orqali)",
      "Faqat o'tirish",
      "Faqat yozish"
    ],
    correctAnswer: "Ko'r va zaif ko'ruvchi bolalarga atrof muhitda mustaqil harakat qilishni o'rgatish (oq tayoq, eshitish orqali)"
  },
  {
    question: "**Oligofrenopedagogikada mehnat ta'limi**ning o'rni?",
    options: [
      "Faqat vaqt o'tkazish",
      "Ijtimoiy-maishiy va oddiy kasbiy ko'nikmalarni shakllantirish, mustaqil hayotga tayyorlash",
      "Faqat yozish",
      "Faqat o'qish"
    ],
    correctAnswer: "Ijtimoiy-maishiy va oddiy kasbiy ko'nikmalarni shakllantirish, mustaqil hayotga tayyorlash"
  },
  {
    question: "**Tayanch-harakat a'zolari nuqsoni bo'lgan bolalar** uchun ta'limdagi asosiy sharoit?",
    options: [
      "Faqat yugurish maydonchasi",
      "Panduslar, liftlar, maxsus mebellar, moslashtirilgan o'quv vositalari (qulay muhit yaratish)",
      "Faqat qora doska",
      "Faqat oddiy stollar"
    ],
    correctAnswer: "Panduslar, liftlar, maxsus mebellar, moslashtirilgan o'quv vositalari (qulay muhit yaratish)"
  },
  {
    question: "**Logopediya nuqtai nazaridan nutqning buzilishi** qaysi turlarga bo'linadi?",
    options: [
      "Faqat o'qish va yozish",
      "Talaffuz, ritm, ovoz, leksika-grammatika va nutqning umumiy rivojlanishidagi buzilishlar",
      "Faqat ko'rish va eshitish",
      "Faqat temperament"
    ],
    correctAnswer: "Talaffuz, ritm, ovoz, leksika-grammatika va nutqning umumiy rivojlanishidagi buzilishlar"
  },
  {
    question: "**Autizm spektridagi buzilishlar (ASB)** bo'lgan bolalar bilan ishlashning asosiy xususiyati?",
    options: [
      "Faqat guruhli ish",
      "Individual yondashuv, xatti-harakatlarni tahlil qilish, ijtimoiy ko'nikmalarni shakllantirish, vizual qo'llab-quvvatlash",
      "Faqat og'zaki dars",
      "Faqat yozish"
    ],
    correctAnswer: "Individual yondashuv, xatti-harakatlarni tahlil qilish, ijtimoiy ko'nikmalarni shakllantirish, vizual qo'llab-quvvatlash"
  },
  {
    question: "Maxsus pedagogikada **'Erta yordam'** nima uchun muhim?",
    options: [
      "Faqat pul tejash",
      "Boladagi rivojlanish nuqsonini erta aniqlash va korreksiyani boshlash orqali kompensatsiya imkoniyatlarini oshirish",
      "Faqat kechikish",
      "Faqat maktab yoshida boshlash"
    ],
    correctAnswer: "Boladagi rivojlanish nuqsonini erta aniqlash va korreksiyani boshlash orqali kompensatsiya imkoniyatlarini oshirish"
  }
];

// ===== GLOBAL O'ZGARUVCHILAR =====
const quizContainer = document.getElementById('quiz-container');
const nextButton = document.getElementById('nextBtn');
const summaryResultsSpan = document.getElementById('summaryResults');
const resultModal = document.getElementById('resultModal');
const continueBtn = document.getElementById('continueBtn');

let shuffledAllQuestions = [];
let currentQuestionIndex = 0;
let totalAttempts = 0;
let correctCount = 0;
let questionAnsweredThisTurn = false;

// 20 ta savollik blok uchun
let blockCorrectCount = 0;
let blockTotalCount = 0;
let blockStartIndex = 0;

// ===== YORDAMCHI FUNKSIYALAR =====
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function updateResults() {
    let percentage = 0;
    if (totalAttempts > 0) {
        percentage = (correctCount / totalAttempts) * 100;
    }
    summaryResultsSpan.textContent = `Urinish: ${totalAttempts}, To'g'ri: ${correctCount}, Foiz: ${percentage.toFixed(0)}%`;
}

function loadQuestion() {
    quizContainer.innerHTML = '';
    questionAnsweredThisTurn = false;
    nextButton.disabled = true;

    if (shuffledAllQuestions.length === 0) {
        shuffledAllQuestions = [...questionsData];
        shuffleArray(shuffledAllQuestions);
        currentQuestionIndex = 0;
    }

    if (currentQuestionIndex >= shuffledAllQuestions.length) {
        currentQuestionIndex = 0;
        shuffleArray(shuffledAllQuestions);
    }

    const q = shuffledAllQuestions[currentQuestionIndex];
    const questionBlock = document.createElement('div');
    questionBlock.classList.add('question-block');

    const questionText = document.createElement('p');
    questionText.classList.add('question-text');
    questionText.textContent = `${totalAttempts + 1}. ${q.question}`;
    questionBlock.appendChild(questionText);

    const optionsList = document.createElement('ul');
    optionsList.classList.add('options-list');

    const shuffledOptions = [...q.options];
    shuffleArray(shuffledOptions);

    shuffledOptions.forEach((option, optionIndex) => {
        const listItem = document.createElement('li');
        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = 'question';
        radioInput.value = option;
        radioInput.id = `q-option${optionIndex}`;

        const label = document.createElement('label');
        label.htmlFor = `q-option${optionIndex}`;
        label.textContent = option;

        radioInput.addEventListener('change', (event) => {
            if (questionAnsweredThisTurn) return;

            const selectedValue = event.target.value;
            const allLabels = questionBlock.querySelectorAll('label');
            
            totalAttempts++;
            blockTotalCount++;

            if (selectedValue === q.correctAnswer) {
                // To'g'ri javob
                label.classList.add('selected-correct');
                correctCount++;
                blockCorrectCount++;

                let feedbackDiv = questionBlock.querySelector('.feedback');
                if (feedbackDiv) feedbackDiv.remove();
                
                feedbackDiv = document.createElement('div');
                feedbackDiv.classList.add('feedback', 'correct');
                feedbackDiv.textContent = 'To\'g\'ri!';
                questionBlock.appendChild(feedbackDiv);
            } else {
                // Noto'g'ri javob
                label.classList.add('selected-wrong');
                
                // To'g'ri javobni ko'rsatish
                allLabels.forEach(lbl => {
                    const radio = document.getElementById(lbl.htmlFor);
                    if (radio && radio.value === q.correctAnswer) {
                        lbl.classList.add('show-correct');
                    }
                });

                let feedbackDiv = questionBlock.querySelector('.feedback');
                if (feedbackDiv) feedbackDiv.remove();
                
                feedbackDiv = document.createElement('div');
                feedbackDiv.classList.add('feedback', 'incorrect');
                feedbackDiv.textContent = `Noto\'g\'ri. To'g'ri javob: "${q.correctAnswer}"`;
                questionBlock.appendChild(feedbackDiv);
            }

            updateResults();

            const radioButtons = questionBlock.querySelectorAll('input[type="radio"]');
            radioButtons.forEach(radio => {
                radio.disabled = true;
            });

            questionAnsweredThisTurn = true;
            nextButton.disabled = false;
        });

        listItem.appendChild(radioInput);
        listItem.appendChild(label);
        optionsList.appendChild(listItem);
    });

    questionBlock.appendChild(optionsList);
    quizContainer.appendChild(questionBlock);
}

function showResultModal() {
    const modalCorrect = document.getElementById('modalCorrect');
    const modalWrong = document.getElementById('modalWrong');
    const modalPercent = document.getElementById('modalPercent');
    const modalVerdict = document.getElementById('modalVerdict');
    const modalIcon = document.querySelector('.modal-icon');

    const wrongCount = blockTotalCount - blockCorrectCount;
    const percentage = blockTotalCount > 0 ? (blockCorrectCount / blockTotalCount) * 100 : 0;

    modalCorrect.textContent = blockCorrectCount;
    modalWrong.textContent = wrongCount;
    modalPercent.textContent = percentage.toFixed(0) + '%';

    // Baholash (70% o'tish bali)
    if (percentage >= 70) {
        modalVerdict.textContent = 'üéâ Tabriklaymiz! Siz imtihondan muvaffaqiyatli o\'tdingiz!';
        modalVerdict.className = 'modal-verdict pass';
        modalIcon.textContent = 'üéâ';
    } else {
        modalVerdict.textContent = 'üòî Afsuski, siz imtihondan o\'ta olmadingiz. Yana harakat qiling!';
        modalVerdict.className = 'modal-verdict fail';
        modalIcon.textContent = 'üòî';
    }

    resultModal.style.display = 'block';
}

function handleNextQuestion() {
    currentQuestionIndex++;
    
    // Har 20 ta savoldan keyin modal ko'rsatish
    if (blockTotalCount > 0 && blockTotalCount % 20 === 0) {
        showResultModal();
        return;
    }

    loadQuestion();
}

// ===== HODISA TINGLOVCHILAR =====
nextButton.addEventListener('click', handleNextQuestion);

continueBtn.addEventListener('click', () => {
    resultModal.style.display = 'none';
    
    // Blok statistikasini tiklash
    blockCorrectCount = 0;
    blockTotalCount = 0;
    blockStartIndex = currentQuestionIndex;
    
    // Yangi savol yuklash
    loadQuestion();
});

// ===== LOGIN TIZIMI =====
window.addEventListener('DOMContentLoaded', function() {
    const isAuthenticated = localStorage.getItem(AUTH_KEY);
    
    if (isAuthenticated === 'true') {
        document.getElementById('loginScreen').classList.add('hidden');
        document.body.classList.remove('login-active');
        startTimer();
        updateResults();
        loadQuestion();
    } else {
        document.body.classList.add('login-active');
        document.getElementById('loginScreen').style.display = 'flex';
    }
});

document.getElementById('loginBtn').addEventListener('click', function() {
    checkCredentials();
});

document.getElementById('password').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        checkCredentials();
    }
});

document.getElementById('username').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('password').focus();
    }
});

function checkCredentials() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    const loginBtn = document.getElementById('loginBtn');
    const btnText = document.getElementById('btnText');

    if (!username || !password) {
        errorMessage.textContent = '‚ö†Ô∏è Iltimos, barcha maydonlarni to\'ldiring!';
        errorMessage.classList.add('show');
        return;
    }

    loginBtn.disabled = true;
    btnText.innerHTML = 'Tekshirilmoqda<span class="loading"></span>';
    errorMessage.classList.remove('show');

    setTimeout(() => {
        if (username === VALID_CREDENTIALS.username && password === VALID_CREDENTIALS.password) {
            localStorage.setItem(AUTH_KEY, 'true');
            errorMessage.classList.remove('show');
            
            btnText.textContent = '‚úì Muvaffaqiyatli!';
            loginBtn.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
            
            setTimeout(() => {
                showMainContent();
            }, 500);
        } else {
            errorMessage.textContent = '‚ùå Login yoki parol noto\'g\'ri!';
            errorMessage.classList.add('show');
            loginBtn.disabled = false;
            btnText.textContent = 'Kirish';
            
            document.getElementById('password').value = '';
            document.getElementById('password').focus();
        }
    }, 500);
}

function showMainContent() {
    const loginScreen = document.getElementById('loginScreen');
    
    loginScreen.style.animation = 'fadeOut 0.5s ease-out';
    
    setTimeout(() => {
        loginScreen.classList.add('hidden');
        document.body.classList.remove('login-active');
        startTimer();
        updateResults();
        loadQuestion();
    }, 500);
}

function logout() {
    if (confirm('Rostdan ham tizimdan chiqmoqchimisiz?')) {
        localStorage.removeItem(AUTH_KEY);
        location.reload();
    }
}

console.log('%cüí° Tizimdan chiqish uchun:', 'color: blue; font-size: 14px; font-weight: bold;');
console.log('%clogout()', 'color: green; font-size: 12px; background: #f0f0f0; padding: 5px;');

// ===== TAYMER =====
let startTime;
let timerInterval;

function startTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
}

function updateTimer() {
    const elapsedTime = Date.now() - startTime;
    const totalSeconds = Math.floor(elapsedTime / 1000);
    
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    const formattedTime = 
        String(minutes).padStart(2, '0') + ':' + 
        String(seconds).padStart(2, '0');

    document.getElementById('timer').textContent = formattedTime;
}