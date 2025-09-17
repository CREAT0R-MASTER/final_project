from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.conf import settings
from .models import Business
import subprocess
import pymysql

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'owner_name', 'is_approved', 'db_name', 'approve_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:business_id>/', self.admin_site.admin_view(self.approve_business), name='approve-business'),
        ]
        return custom_urls + urls

    def approve_button(self, obj):
        if not obj.is_approved:
            url = reverse('admin:approve-business', args=[obj.id])
            return format_html(f'<a class="button" href="{url}">✅ Approve</a>')
        return format_html('<span style="color:green;">✔ Approved</span>')
    approve_button.short_description = 'Approval'

    def approve_business(self, request, business_id):
        try:
            business = Business.objects.get(id=business_id)
            if business.is_approved:
                self.message_user(request, "Already approved.", level=messages.WARNING)
                return redirect("..")

            db_name = f"tenant_{business.name.lower().replace(' ', '_')}"
            business.db_name = db_name

            # Step 1: Create the tenant DB
            root_conn = pymysql.connect(
                host=settings.DATABASES['default']['HOST'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                charset='utf8mb4',
                autocommit=True
            )
            with root_conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            root_conn.close()

            # Step 2: Dump schema using mysqldump
            dump_result = subprocess.run([
                "mysqldump",
                "-u", settings.DATABASES['default']['USER'],
                f"--password={settings.DATABASES['default']['PASSWORD']}",
                "--no-data",
                settings.DATABASES['default']['NAME']
            ], capture_output=True, text=True)

            if dump_result.returncode != 0:
                self.message_user(request, f"Schema dump failed:\n{dump_result.stderr}", level=messages.ERROR)
                return redirect("..")

            schema_sql = dump_result.stdout

            # Step 3: Execute schema into the new DB
            tenant_conn = pymysql.connect(
                host=settings.DATABASES['default']['HOST'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                database=db_name,
                charset='utf8mb4',
                autocommit=True
            )
            with tenant_conn.cursor() as cursor:
                for statement in schema_sql.split(";\n"):
                    if statement.strip():
                        cursor.execute(statement)
            tenant_conn.close()

            # Step 4: Approve and save business
            business.is_approved = True
            business.save()

            self.message_user(request, f"Business '{business.name}' approved and tenant DB '{db_name}' created ✅", level=messages.SUCCESS)
            return redirect("..")

        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level=messages.ERROR)
            return redirect("..")
