from typing import List
import torch
from tqdm.auto import tqdm
from transformers import BertTokenizerFast, BertForSequenceClassification
import re
import torch.nn as nn
from transformers import BertTokenizerFast, BertForSequenceClassification, BertModel


CLEAN_HTML = re.compile('<.*?>')
CLEAN_CLUB = re.compile('\[club.*?\]')
CLEAN_ID = re.compile('\[id.*?\]')
CLEAN_UNAME = re.compile('@[^\s]+')

def clean_text(text):
    text = text.strip("'")
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\xa0', ' ')
    text = re.sub(CLEAN_CLUB, ' ', text)
    text = re.sub(CLEAN_ID, ' ', text)
    text = re.sub(CLEAN_HTML, ' ', text)
    text = re.sub(CLEAN_UNAME, ' ', text)
    text = text.replace('Здравствуйте' , ' ').replace('Добрый день' , ' ').replace('Доброго времени суток' , ' ').replace('Добрый вечер' , ' ')
    text = text.replace('Доброе утро' , ' ')
    text = text.replace('>', ' ')
    text = text.strip().lstrip('.')
    text = text.strip().lstrip('!')
    text = text.strip().lstrip(',')
    text = text.strip()
    return text


device = 'cuda' if torch.cuda.is_available() else 'cpu'
device = torch.device(device)

tokenizer = BertTokenizerFast.from_pretrained('ai-forever/ruBert-large')

executor_label = (
    'Лысьвенский городской округ',
    'Министерство социального развития ПК',
    'Город Пермь',
    'Министерство здравоохранения',
    'АО ПРО ТКО',
    'Министерство образования',
    'ИГЖН ПК',
    'Бардымский муниципальный округ Пермского края',
    'Александровский муниципальный округ Пермского края',
    'Губахинский городской округ'
)

theme_group_label = (
    'Благоустройство',
    'Социальное обслуживание и защита',
    'Общественный транспорт',
    'Здравоохранение/Медицина',
    'Мусор/Свалки/ТКО',
    'Образование',
    'Дороги',
    'ЖКХ',
    'Коронавирус',
    'Экономика и бизнес',
    'Культура',
    'Связь и телевидение',
    'Газ и топливо',
    'Безопасность',
    'Спецпроекты',
    'Мобилизация',
    'МФЦ "Мои документы"',
    'Физическая культура и спорт',
    'Торговля',
    'Строительство и архитектура',
    'Памятники и объекты культурного наследия',
    'Экология',
    'Государственная собственность',
    'Роспотребнадзор',
    'Погребение и похоронное дело',
    'Электроснабжение'
)

theme_label = (
    '★ Ямы во дворах',
    'Оказание гос. соц. помощи',
    'Дети и многодетные семьи',
    'Содержание остановок',
    'Технические проблемы с записью на прием к врачу',
    'Плата за вывоз ТКО',
    'Образовательный процесс',
    'Диспансеризация',
    '★ Просьбы о лечении',
    '★ Нарушение правил очистки дорог от снега и наледи/Обращения о необходимости очистить тротуар от снега и наледи',
    'Предложение по благоустройству',
    'Задержка выплат гражданам',
    'Аварийное жилье/переселение',
    '★ Нарушение правил уборки от снега и наледи внутридворового проезда, тротуара, площади',
    'Жалобы на управляющие компании',
    'Борщевик Сосновского',
    'Пешеходные переходы и жд переезды',
    '★ Уборка/Вывоз мусора',
    'Жалобы на врачей',
    'Трудоустройство',
    'Подтопление автомобильных дорог',
    'Тесты на коронавирус',
    '★ Оказание медицинской помощи не в полном объеме/отказ в оказании медицинской помощи',
    'Парки и зоны отдыха',
    'Содержание больниц',
    'Уборка территорий',
    '★ Отсутствие контейнерной площадки/Проезд к контейнерной площадке',
    'Благоустройство общественного пространства (парк, сквер, пешеходная зона, бульвар, набережная, центральная улица или площадь)',
    '★ Питание в медицинских учреждениях',
    'Нехватка или сокращение врачей и медицинских учреждений',
    'Необходима установка и замена дорожных ограждений',
    '★ Ненадлежащее содержание зеленых насаждений (газонов)/деревьев и кустарников',
    'Вырубка деревьев, кустарников',
    'Предложить установку нового лежачего полицейского (ИДН)',
    'Цены и ценообразование',
    'Учреждения культуры',
    'Профильный осмотр',
    'Доступность вакцин',
    'Плата за ЖКУ и работа ЕИРЦ',
    'Культурно-досуговые мероприятия',
    'Отсутствие холодной воды',
    'Ремонт/строительство мостов',
    'Завышение платы за коммунальные услуги',
    'Очередь',
    'Ненадлежащее качество или отсутствие отопления',
    'Организация парковок',
    'Ненадлежащая уборка подъездов и лифтов',
    'Коронавирус',
    'Неудовлетворительные условия проезда в транспорте на действующем маршруте',
    'Содержание, ремонт и обустройство тротуаров',
    'Отсутствие лекарств в аптеках',
    'Порядок и пункты вакцинации',
    '★ Информационно-техническая поддержка',
    'Восстановление газоснабжения',
    'Отсутствие горячей воды',
    'Некачественный капитальный ремонт',
    'Ошибки врачей, халатность',
    'Создание доступной среды для инвалидов',
    '★ Неисправные фонари освещения',
    '★ Скорая помощь',
    'Сборы за капитальный ремонт',
    'Социальные учреждения',
    'Безопасность общественных пространств',
    'Льготные лекарства',
    'Проблемы с контейнерами',
    'Ямы и выбоины на дороге',
    'Дезинфекция МКД',
    'Вакцинация',
    '★ Затопление подъездов, подвальных помещений',
    'Строительство или реконструкция дорог',
    'Отсутствие фонарей освещения',
    'Ремонт дороги',
    'Занятость и трудоустройство',
    '★ Некачественно нанесенная разметка на проезжей части',
    'Разрушение тротуаров и пешеходных дорожек',
    'Отсутствие детских площадок',
    'Ливневые канализации (строительство и реконструкция)',
    'Отлов безнадзорных собак и кошек',
    'Некорректное поведение водительского состава',
    'Плохое качество воды',
    'Спецпроекты',
    'Льготы на проезд и тарифы',
    'Поддержка семей мобилизованных',
    'Инвалиды',
    '★ Нарушение правил уборки от снега и наледи территории парка и сквера',
    '★ Наледь и сосульки на кровле',
    'График движения общественного транспорта',
    'Пенсионеры и ветераны',
    'Государственные услуги',
    '★ Отсутствие урн, лавочек в общественных местах и дворовой территории',
    'Детские оздоровительные лагеря',
    'Низкая температура воды/слабое давление',
    'Строительство спортивной инфраструктуры',
    '★ Прорыв трубы/трубопровода',
    '★ Открытые канализационные люки',
    'Безопасность образовательного процесса',
    'Нарушение правил проведения земляных работ',
    'Хамство медицинских работников',
    'Зарплата, компенсации, поощрения, выплаты',
    'Зарплата учителей',
    'Добавить новый маршрут',
    '★ Нестационарная торговля (киоски, павильоны, сезонная торговля)',
    '★ Нарушение правил уборки и вывоза порубочных остатков',
    'Ненадлежащее содержание и эксплуатация МКД',
    'Перепланировка и реконструкция помещений',
    'Дополнительное образование',
    'Дистанционное образование',
    'Строительство объектов по обращению с отходами',
    'Отсутствие электричества',
    'Отсутствие лекарств в стационарах',
    '★ Несанкционированные надписи, рисунки, реклама на фасаде МКД',
    'Освещение неисправно или отсутствует',
    'Непригодные для проживания жилые помещения',
    '★ Протечки с кровли (системы водостока)',
    'Обустройство асфальтового покрытия парковки, внутридворового проезда, тротуара, пешеходной дорожки, въезда во двор',
    'Низкая заработная плата врачей',
    'Раздельная сортировка отходов',
    'Организация переходов, светофоров/Изменить организацию движения',
    'Состояние зданий учреждений и организаций',
    'Ремонт спортивных учреждений',
    'Памятники и объекты культурного наследия',
    'Общее впечатление',
    'Благоустройство придомовых территорий',
    'Строительство школ, детских садов',
    'Запрос на газификацию и её условия',
    'Улучшение жилищных условий',
    'Нехватка материально-технического обеспечения',
    'Работа светофора (установка, изменение режима работы, оборудование кнопкой вызова)',
    'Нехватка мест в школах',
    'Отсутствие остановочных пунктов',
    'Содержание гос. образовательных организаций',
    'Выбросы вредных веществ в атмосферу/загрязнение воздуха',
    '★ Нарушение правил уборки и вывоза загрязненного снега и наледи на газоне',
    'Сертификаты и QR-коды',
    '★ Ненадлежащее состояние игровых элементов на детской или спортивной площадке',
    '★ Несоблюдение правил уборки проезжей части',
    'Волонтерство',
    'Проблемы с социальными картами или проездными документами',
    'Проблемы в работе горячих линий',
    '★ Подтопление территории',
    'Социальная поддержка медперсонала',
    'ВУЗы и ССУЗы',
    'Строительство социальных объектов',
    'Коронавирусные ограничения',
    'Питание',
    'ЕГЭ, ОГЭ',
    'Содержание дорожных знаков/Установка новых дорожных знаков, с внесением в схему дислокации, замена старых знаков на новые',
    'Спортивные мероприятия',
    'Строительство зданий',
    'Выплаты стипендий',
    'Нарушение технологии и (или) сроков производства работ',
    'Выбросы вредных веществ в водоёмы/загрязнение водоёмов',
    'Изменение класса и количества автобусов',
    'Самоизоляция и карантин',
    'Подключение к водоснабжению',
    'Региональное имущество',
    'Изменить или отменить маршрут',
    'Пробки',
    '★ Нарушение правил уборки внутридворового проезда, пешеходной дорожки',
    'Предложение дороги в план ремонта',
    'Отсутствие аптек',
    'Выброс мусора нарушителем',
    'Ремонт подъездов',
    'Санитарно-эпидемиологическое благополучие',
    'Предложения по созданию лечебных центров',
    'Проблемы с отоплением детских садов и школ',
    '★ Стихийные свалки в городе/в парках/в лесу',
    'Ненадлежащее состояние фасадов нежилых зданий, объектов и ограждений',
    'Обработка и уничтожение грызунов (дератизация)',
    'Погребение и похоронное дело',
    'Другие проблемы с общедомовой системой водоотведения (канализации)',
    'Качество электроснабжения',
    'Отсутствие общественных туалетов',
    'Беженцы',
    'МФЦ "Мои документы"',
    '★ Засор в общедомовой системе водоотведения (канализации)',
    'Несанкционированное ограничение движения, помехи движению, захват земли в полосе отвода автодорог',
    'Архитектура города',
    'Социальная поддержка учителей',
    'Установка ограждений, препятствующих въезду на тротуар, газон на дворовой территории МКД',
    'Лифт неисправен или отключен',
    'Самовольная установка ограждений на территории общего пользования',
    'Кадровые перестановки',
    'Некачественно выполненный ремонт дорог',
    'Здравоохранение прочее',
    '★ Повреждение опор ЛЭП',
    'Сроки газификации',
    'Стоимость, оплата и возврат средств на газификацию',
    '★ Нарушение правил уборки от снега и наледи детской игровой и спортивной площадки',
    'Залитие квартиры',
    'Неисправность выступающих конструкций: балконов, козырьков, эркеров, карнизов входных крылец и т. п.',
    'Соц.обслуживание прочее',
    'Устройство в ДОУ',
    '★ Парковка на газонах',
    'Матери-одиночки, подростки'
)

class JointClassifier(nn.Module):
    def __init__(self, model_name: str = 'ai-forever/ruBert-large', dropout: float = .1):
        super(JointClassifier, self).__init__()
        self.language_model = BertModel.from_pretrained(model_name)
        self.executor_cls = nn.Sequential(
            nn.BatchNorm1d(1024),
            nn.Dropout(p=dropout),
            nn.SiLU(),
            nn.Linear(1024, 10),
        )
        self.theme_group_cls = nn.Sequential(
            nn.BatchNorm1d(1024),
            nn.Dropout(p=dropout),
            nn.SiLU(),
            nn.Linear(1024, 26),
        )
        self.theme_cls = nn.Sequential(
            nn.BatchNorm1d(1024 + 26),
            nn.Dropout(p=dropout),
            nn.SiLU(),
            nn.Linear(1024 + 26, 195),
        )

    def forward(self, input_ids, attention_mask):
        output = self.language_model(input_ids=input_ids, attention_mask=attention_mask).pooler_output
        executor_logits = self.executor_cls(output)
        theme_group_logits = self.theme_group_cls(output)
        theme_inputs = torch.cat(
            (output, theme_group_logits), 1
        )
        theme_logits = self.theme_cls(theme_inputs)
        return executor_logits, theme_group_logits, theme_logits


tokenizer = BertTokenizerFast.from_pretrained('ai-forever/ruBert-large')
model = JointClassifier()
model.load_state_dict(torch.load('../models/latest.pt'))
model.eval()
model.to(device)


def predict(texts: List[str]) -> List[str]:
    """предикт по трём категориям"""
    texts = [clean_text(t) for t in texts]
    executor_labels, theme_group_labels, theme_labels = [], [], []
    for step in range(0, len(texts), 50):
        batch = texts[step:step+50]
        inputs = tokenizer(
            batch,
            padding='max_length',
            truncation=True,
            max_length=512,
            return_token_type_ids=False,
            return_tensors='pt')
        with torch.no_grad():
            executor_logits, theme_group_logits, theme_logits = model(inputs['input_ids'].to(device), inputs['attention_mask'].to(device))
        
        executor_preds = torch.argmax(torch.softmax(executor_logits.detach().cpu(), dim=-1), dim=-1)
        theme_group_preds = torch.argmax(torch.softmax(theme_group_logits.detach().cpu(), dim=-1), dim=-1)
        theme_preds = torch.argmax(torch.softmax(theme_logits.detach().cpu(), dim=-1), dim=-1)
        
        executor_labels.extend(executor_preds.tolist())
        theme_group_labels.extend(theme_group_preds.tolist())
        theme_labels.extend(theme_preds.tolist())
    
    executor_labels = [executor_label[l] for l in executor_labels]
    theme_group_labels = [theme_group_label[l] for l in theme_group_labels]
    theme_labels = [theme_label[l] for l in theme_labels]
    return executor_labels, theme_group_labels, theme_labels
