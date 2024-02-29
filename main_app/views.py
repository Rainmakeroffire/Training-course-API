from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Product, Lesson, Group
from django.contrib.auth.models import User
from .serializers import ProductSerializer, LessonSerializer


def distribute_student(groups):
    """
    Вспомогательная функция для распределения студентов по группам перед началом учебного курса.

    Алгоритм распределяет студентов так, чтобы в каждой группе количество участников не отличалось больше, чем на 1,
    учтиывая при этом минимальные и максимальные значения участников в группе.
    """
    # Объявляем переменные для целевой группы и минимального количества студентов в группе
    target_group = None
    min_student_count = float('inf')

    # Итерируемся по группам и находим группу с минимальным числом студентов
    for group in groups:
        if group.students.count() < min_student_count:
            target_group = group
            min_student_count = group.students.count()

    # Если количество студентов в целевой группе меньше максимального допустимого количества,
    # возвращаем эту группу для добавления студента
    if target_group.students.count() < target_group.product.max_group_capacity:
        return target_group
    else:
        return None


@login_required
def signup_for_course(request, product_id):
    """API для записи студента на учебный курс."""
    if request.method == 'POST':
        # Получаем данные о текущем пользователе, курсе и группах
        user = request.user
        product = get_object_or_404(Product, id=product_id)
        groups = Group.objects.filter(product=product)

        # Если учебный курс уже начался, записываем студента в первую доступную группу
        if product.starts_at < timezone.now():
            for group in groups:
                if group.students.count() < group.product.max_group_capacity:
                    group.students.add(user)
                    return JsonResponse({'success': True, 'message': 'Вы успешно записаны на курс.'})
        # В противном случае находим студенту подходящую группу по алгоритму и записываем в неё
        else:
            group = distribute_student(groups)
            if group:
                group.students.add(user)
                return JsonResponse({'success': True, 'message': 'Вы успешно записаны на курс.'})

        # сообщаем пользователю, что записать запись не удалась
        return JsonResponse({'success': False, 'error': 'Не удалось записаться, запись на курс закончена.'},
                            status=400)


def get_products(request):
    """
    API на список продуктов, доступных для покупки, включающее основную информацию о продукте и количество уроков,
    которые принадлежат продукту.
    """
    if request.method == 'GET':
        # Получение всех продуктов с предварительной загрузкой связанных уроков для оптимизации запроса
        products = Product.objects.prefetch_related('lessons').all()

        # Сериализация каждого продукта и подсчёт количества уроков
        serialized_products = []
        for product in products:
            product_data = ProductSerializer(product).data
            product_data['lesson_count'] = product.lessons.count()
            serialized_products.append(product_data)
        return JsonResponse(serialized_products, safe=False)


@login_required
def get_available_lessons(request, product_id):
    """API с выведением списка уроков по конкретному продукту, к которому пользователь имеет доступ."""
    if request.method == 'GET':
        # Получение курса по идентификатору
        product = get_object_or_404(Product, id=product_id)

        # Проверка, имеет ли текущий пользователь доступ к курсу и получение всех уроков по этому курсу
        if request.user in product.allowed_users.all():
            lessons = Lesson.objects.filter(product=product)

            # Сериализация уроков и добавление информации о продукте к каждому уроку
            product_data = ProductSerializer(product).data
            serialized_lessons = LessonSerializer(lessons, many=True)
            data = serialized_lessons.data
            for lesson_data in data:
                lesson_data['product'] = product_data

            # Возврат JSON-ответа с данными о доступных уроках для продукта
            return JsonResponse(data, safe=False)
        else:
            # Возврат JSON-ответа с ошибкой доступа
            return JsonResponse({'error': 'Вы не имеете доступа к этому курсу.'}, status=403)


def get_stats(request):
    """
    API для получения статистики по продуктам на платформе.

    Возвращает список всех продуктов на платформе вместе с информацией о количестве учеников,
    проценте заполненности групп и проценте приобретения продукта.

    """
    if request.method == 'GET':
        # Получаем все продукты и колчество пользователей на платформе, создаём список статистики
        products = Product.objects.prefetch_related('groups__students', 'allowed_users').all()
        total_users = User.objects.count()
        stats = []

        for product in products:
            # Получаем количество учеников, занимающихся на продукте
            student_count = product.allowed_users.count()

            # Рассчитываем процент заполненности групп
            total_group_capacity = product.groups.count() * product.max_group_capacity
            actual_occupancy = sum(group.students.count() for group in product.groups.all())
            occupancy_rate = round((actual_occupancy / total_group_capacity) * 100, 2) if total_group_capacity > 0 \
                else 0

            # Рассчитываем процент приобретения продукта
            purchase_rate = round((student_count / total_users) * 100, 2) if total_users > 0 else 0

            # Собираем информацию о статистике по продукту
            product_stats = {
                'id': product.id,
                'name': product.name,
                'student_count': student_count,
                'occupancy_rate': occupancy_rate,
                'purchase_rate': purchase_rate,
            }

            # Добавляем информацию о продукте в список статистики
            stats.append(product_stats)

        return JsonResponse(stats, safe=False)
