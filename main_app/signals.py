from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Group, Product


@receiver(m2m_changed, sender=Group.students.through)
def validate_max_group_capacity(sender, instance, action, pk_set, **kwargs):
    """
    Сигнал для проверки максимального количества студентов в группе перед добавлением или удалением студентов.

    Проверяет, не превышает ли количество студентов в группе максимальное допустимое количество,
    указанное в поле max_group_capacity объекта Product, связанного с данной группой.

    Raises:
    ValidationError: Возникает, если количество студентов в группе превышает максимальное допустимое значение.
    """
    if action in ['pre_add', 'pre_remove'] and sender == Group.students.through:
        # Получаем связанный объект Product
        product = instance.product
        if product:
            # Определяем количество новых студентов, которые будут добавлены или удалены
            new_students_count = len(pk_set) if action == 'pre_add' else 0

            # Проверяем, не превышает ли общее количество студентов в группе максимальное допустимое значение
            if instance.students.count() + new_students_count > product.max_group_capacity:
                raise ValidationError(
                    f"Максимальное количество студентов в группе - {product.max_group_capacity}.")


@receiver(m2m_changed, sender=Group.students.through)
def update_allowed_users(sender, instance, action, pk_set, **kwargs):
    """
    Сигнал для обновления списка пользователей, имеющих доступ к курсу, на основе изменений в группе студентов.

    Обновляет список пользователей, имеющих доступ к курсу, в соответствии с изменениями в группе студентов.
    """

    if action in ['post_add', 'post_remove'] and sender == Group.students.through:
        # Получаем связанный объект Product
        product = instance.product
        if product:
            if action == 'post_add':
                # Получаем новых студентов, добавленных в группу, и добавляем их в список пользователей,
                # имеющих доступ к продукту
                new_students = instance.students.filter(pk__in=pk_set)
                product.allowed_users.add(*new_students)
            else:
                # Получаем студентов, удаленных из группы, и удаляем их из списка пользователей,
                # имеющих доступ к продукту
                removed_students = instance.students.filter(pk__in=pk_set)
                product.allowed_users.remove(*removed_students)


@receiver(m2m_changed, sender=Product.allowed_users.through)
def update_students(sender, instance, action, pk_set, **kwargs):
    """
    Сигнал для удаления из групп студентов, которые утратили доступ к учебному курсу.

    Если студент утратил доступ к учебному курсу, он удаляется из всех групп, связанных с данным курсом.
    """
    if action == 'post_remove' and sender == Product.allowed_users.through:
        # Получаем все группы, связанные с этим продуктом
        groups = Group.objects.filter(product=instance)
        # Итерируемся по каждой группе и удаляем из нее удаленных пользователей
        for group in groups:
            group.students.remove(*pk_set)

