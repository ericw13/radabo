# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-23 15:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Argument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(blank=True, max_length=30, null=True)),
                ('options', models.CharField(blank=True, max_length=1024, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('directory_path', models.CharField(max_length=255)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='FileTransfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('N', 'New'), ('I', 'In Process'), ('C', 'Complete'), ('E', 'Error')], default='N', max_length=1)),
                ('error_message', models.CharField(blank=True, max_length=1000, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'files transferred',
            },
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_alias', models.CharField(max_length=50, unique=True)),
                ('host_name', models.CharField(max_length=255)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Login',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=64)),
                ('account_description', models.CharField(blank=True, max_length=255, null=True)),
                ('port', models.IntegerField(blank=True, null=True)),
                ('password', models.CharField(blank=True, max_length=32, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.Host')),
            ],
        ),
        migrations.CreateModel(
            name='NotificationList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list_name', models.CharField(max_length=50, unique=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'notification lists',
            },
        ),
        migrations.CreateModel(
            name='NotificationUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive')], default='A', max_length=1)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
                ('notification_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.NotificationList')),
            ],
            options={
                'verbose_name_plural': 'notified users',
            },
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('process_name', models.CharField(max_length=64, unique=True)),
                ('script_location', models.CharField(max_length=255)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TransferLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_code', models.CharField(max_length=30, unique=True)),
                ('transfer_direction', models.CharField(choices=[('PUSH', 'Push'), ('PULL', 'Pull')], default='PULL', max_length=4)),
                ('current_suffix', models.CharField(blank=True, max_length=50, null=True)),
                ('local_rename_suffix', models.CharField(blank=True, max_length=50, null=True)),
                ('remote_rename_suffix', models.CharField(blank=True, max_length=50, null=True)),
                ('auto_transfer_enabled', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='Y', max_length=1)),
                ('filename_mask', models.CharField(blank=True, max_length=50, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
                ('archive_directory', models.ForeignKey(blank=True, db_column='archive_directory', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='archive_dir', to='xfrAdmin.Directory')),
                ('local_directory', models.ForeignKey(db_column='local_directory', default=-1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='local_dir', to='xfrAdmin.Directory')),
                ('login', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='remote_host', chained_model_field='host', on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.Login')),
                ('notification_list', models.ForeignKey(blank=True, db_column='notification_list', null=True, on_delete=django.db.models.deletion.SET_NULL, to='xfrAdmin.NotificationList')),
                ('process', models.ForeignKey(db_column='process', default=-1, on_delete=django.db.models.deletion.SET_DEFAULT, to='xfrAdmin.Process')),
                ('remote_directory', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='remote_host', chained_model_field='host', db_column='remote_directory', default=-1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='remote_dir', to='xfrAdmin.Directory')),
                ('remote_host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.Host')),
            ],
            options={
                'verbose_name_plural': 'transfer locations',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sso_user_id', models.CharField(max_length=20, unique=True)),
                ('email_address', models.CharField(max_length=100, unique=True)),
                ('user_name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive')], default='A', max_length=1)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='notificationuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.User'),
        ),
        migrations.AddField(
            model_name='filetransfer',
            name='location',
            field=models.ForeignKey(default=-1, on_delete=django.db.models.deletion.SET_DEFAULT, to='xfrAdmin.TransferLocation'),
        ),
        migrations.AddField(
            model_name='directory',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.Host'),
        ),
        migrations.AddField(
            model_name='argument',
            name='process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xfrAdmin.Process'),
        ),
        migrations.AlterUniqueTogether(
            name='notificationuser',
            unique_together=set([('notification_list', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='login',
            unique_together=set([('host', 'user_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='directory',
            unique_together=set([('host', 'directory_path')]),
        ),
        migrations.AlterUniqueTogether(
            name='argument',
            unique_together=set([('process', 'command')]),
        ),
    ]
