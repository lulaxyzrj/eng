import { Component, OnInit } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import { FormControl, FormGroup } from '@angular/forms';
import { Location } from '@angular/common';
import { TaskService } from 'src/app/features/task/service/task.service';
import { ToastService } from 'src/app/shared/service/toast.service';
import { FormlyFieldConfig } from '@ngx-formly/core';
import { FilterTask } from 'src/app/features/task/model/task-filterdata';

@Component({
    selector: 'task-list',
    templateUrl: './task-list.component.html',
    styleUrls: ['./task-list.component.scss'],
})
export class TaskListComponent implements OnInit {
    subscription: Subscription;
    formFilter = new FormGroup({});
    fields: FormlyFieldConfig[] = [];
    model: FilterTask;
    filterTaskActivity: FilterTask;
    cols: any[];
    taskList: any[];
    
    constructor(public translate: TranslateService,
                //public grmModuleService: GrmModuleService,
                //private confirmationService: ConfirmationService,
                private toast: ToastService,
                private taskService: TaskService,
                private _location: Location) {
    }

    ngOnInit(): void {
        this.initModelFilter();
        this.initFilterForm();
        this.iniSubscription();
        this.search();
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    back() {
        this._location.back();
    }

    search() {
        this.taskService.getAll().subscribe(
            data => {
                if (data) {
                    this.taskList = data;
                    this.filterSearch();
                }
            },
            err => {
                this.toast.showError(err.message);
            }
        );
    }

    inactivate(id: number) {
        this.taskService.inactivate(id);
    }

    reactivate(id: number) {
        this.taskService.reactivate(id);
    }

    filterSearch() {
        this.taskList = this.taskList
                .filter(item => (this.model.name !== undefined && this.model.name !== '') ? item.name.toLowerCase().includes(this.model.name.toLowerCase()) : true);
        
        if (this.formFilter.controls.activeInput.value !== undefined && this.formFilter.controls.activeInput.value !== '' && this.formFilter.controls.activeInput.value !== null && this.formFilter.controls.activeInput.value !== 'all') {
            this.taskList =  this.taskList.filter(item => item.active === Boolean(JSON.parse(this.formFilter.controls.activeInput.value)) );
        }
    }

    initModelFilter() {
        this.model = { ...this.filterTaskActivity};
        this.model.active = true;
        this.model.activeInput = 'true';
    }

    initFilterForm() {
        this.formFilter = new FormGroup({
            activeInput: new FormControl('true')
        });

        this.fields = [
            {
                className: 'col-md-6 custom-form-col',
                name: 'name',
                key: 'name',
                type: 'input',
                templateOptions: {
                    label: 'Nome',
                    required: false,
                    type: 'text'
                }
            }
        ];
    }

    iniSubscription() {
        this.subscription = this.taskService.allTasks$.subscribe(
            data => {
                if (data) {
                    this.taskList = data;
                }
            },
            err => {
                this.toast.showError(err.message);
            }
        );
        this.taskService.getAll().subscribe(
            data => {
                if (data) {
                    this.taskList = data;
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

    create() {
        window.location.href = '/tasks/new';
    }

    edit(task: any) {
        window.location.href = '/tasks/edit/' + task.id;
    }
}
