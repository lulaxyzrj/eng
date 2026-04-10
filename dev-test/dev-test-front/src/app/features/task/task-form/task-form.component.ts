import { Component, OnInit } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import { FormControl, FormGroup } from '@angular/forms';
import { FormlyFieldConfig } from '@ngx-formly/core';
import { ConfirmationService, DialogService } from 'primeng';
import { Task } from 'src/app/features/task/model/task';
import { Activity } from 'src/app/features/activity/model/activity';
import { TaskService } from 'src/app/features/task/service/task.service';
import { ToastService } from 'src/app/shared/service/toast.service';
import { AddActivityDialogComponent } from '../add-activity-dialog/add-activity-dialog.component';
import { ActivityService } from '../../activity/service/activity.service';

@Component({
    selector: 'task-form',
    templateUrl: './task-form.component.html',
    styleUrls: ['./task-form.component.scss'],
})
export class TaskFormComponent implements OnInit {
    subscription: Subscription;
    form = new FormGroup({});
    fields: FormlyFieldConfig[] = [];
    model: Task;
    cols: any[];
    taskActivitiesList: any[];
    taskTypeList: any[];
    activitiesList: Activity[] = [];
    allEquipmentTypes: any[];
    allReason: any[];
    taskId: number | null;
    isEditing = false;
    isLoading = true;

    constructor(public translate: TranslateService,
                private confirmationService: ConfirmationService,
                private activityService: ActivityService,
                private toast: ToastService,
                private taskService: TaskService,
                private dialogService: DialogService) {
    }

    ngOnInit(): void {
        this.model = {...this.model};
        this.initForm();
        this.iniSubscription();
        this.initFieldValues();
        this.isLoading = false;
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    back() {
        window.location.href = '/tasks/';
    }

    initForm() {
        this.form = new FormGroup({
            locationIsMandatory: new FormControl()
        });
        this.fields = [
            {
                className: 'col-md-6 custom-form-col',
                name: 'name',
                key: 'name',
                type: 'input',
                templateOptions: {
                    label: 'Nome',
                    required: true,
                    type: 'text'
                }
            },
            {
                className: 'col-md-6 custom-form-col',
                name: 'description',
                key: 'description',
                type: 'input',
                templateOptions: {
                    label: 'Descrição',
                    required: true,
                    type: 'text'
                }
            }
        ];

        this.taskId = this.getIdFromUrl();
    }

    iniSubscription() {
        this.subscription = this.activityService.getAll().subscribe(
            data => {
                if (data) {
                    this.taskActivitiesList = data;
                }
            },
            err => {
                this.toast.showError(err.message);
            }
        );
    }

    showError(err: any) {
        let msg = '';

        if (err.error && err.error.message !== null) {
            msg = err.error.message !== undefined ? err.error.message : err.error;
        } else if (err.message) {
            msg = err.message;
        }

        this.toast.showError(msg);
    }

    addActivity(activity: any) {
        const ref = this.dialogService.open(AddActivityDialogComponent, {
            header: 'Adicionar Atividade',
            contentStyle: {
                'overflow-x': 'hidden',
                'overflow-y': 'hidden'
            },
            width: '540px',
            height: '40%',
            closeOnEscape: true,
            dismissableMask: true,
            data: [ activity, this.taskActivitiesList ]
        });
        ref.onClose.subscribe(activitySelected => {
 
        });
    }

    remove(activity: any) {
        
    }

    getEquipmentTypesByActivity(activity) {

    }

    saveTask() {
        this.isLoading = true;

        const task = {
            id: this.model.id,
            name: this.model.name,
            description: this.model.description,
            active: this.model.active
        };

        this.taskService.save(task).subscribe({
            next: result => {
                this.isLoading = false;
                this.back();
            },
            error: err => {
                this.isLoading = false;
                this.showError(err);
            }
        });
    }

    getIdFromUrl() {
        const url = window.location.href;
        if (!isNaN((url.substring(url.lastIndexOf('/') + 1)) as any)) {
            return parseInt(url.substring(url.lastIndexOf('/') + 1), 10);
        }
        return null;
    }

    initFieldValues() {
        if (this.taskId != null) {
            this.isLoading = true;
            this.taskService.getById(this.taskId).subscribe(
                result => {
                    if (result) {
                        this.model = result;
                        this.isEditing = true;
                        this.isLoading = false;
                    }
                },
                err => {
                    this.showError(err);
                }
            );
        }
    }
}
