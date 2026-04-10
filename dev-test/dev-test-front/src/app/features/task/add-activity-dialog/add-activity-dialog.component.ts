import {Component, OnInit} from '@angular/core';
import {DialogService} from 'primeng';
import {FormlyFieldConfig} from '@ngx-formly/core';
import {FormControl, FormGroup} from '@angular/forms';
import {DynamicDialogConfig, DynamicDialogRef} from 'primeng/dynamicdialog';
import {of} from 'rxjs';
import { TaskActivity } from 'src/app/features/task/model/task-activity';
import { Task } from 'src/app/features/task/model/task';

@Component({
    selector: 'add-activity-dialog',
    templateUrl: './add-activity-dialog.component.html',
    styleUrls: ['./add-activity-dialog.component.scss'],
    providers: [DialogService]
})
export class AddActivityDialogComponent implements OnInit {

    form = new FormGroup({});
    fields: FormlyFieldConfig[] = [];
    model = new TaskActivity();
    allTaskTypes: Task[];
    allTaskActivityListObservable$ = of([]);
    activitySeleted: any;

    constructor(
        public dynamicDialogRef: DynamicDialogRef,
        public dynamicDialogConfig: DynamicDialogConfig
    ) {
    }

    ngOnInit(): void {
        this.initFields();
    }

    initFields() {
        this.form = new FormGroup({
           activityId: new FormControl(),
        });

        this.fields = [
            {
                className: 'col-md-12 custom-form-col',
                key: 'activityId',
                type: 'lup-select',
                templateOptions: {
                    multiple: false,
                    label: 'Atividade',
                    placeholder: 'Selecione a atividade',
                    bindValue: 'id',
                    bindLabel: 'name',
                    required: true,
                    disabled: false,
                    horizontalTemplate: false,
                    options$: this.allTaskActivityListObservable$
                }
            }
        ];

    }

    cancel() {
        this.close(null);
    }

    add() {
        this.model.activityId = this.form.controls.activityId.value;
        this.close(this.model);
    }

    close(activity: any) {
        if (this.dynamicDialogRef) {
            this.dynamicDialogRef.close(activity);
        }
    }

    isFormValid() {
        const isValid = this.form.controls.activityId && this.form.controls.activityId.value != null;
        if (!isValid) {
            return false;
        }
        return true;
    }
}
