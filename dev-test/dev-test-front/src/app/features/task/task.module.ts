import {CUSTOM_ELEMENTS_SCHEMA, Injector, NgModule} from '@angular/core';
import { StoreModule } from '@ngrx/store';
import { reducerTask } from './state/task.reducer';
import { TaskSelectors } from './state/task.selectors';
import { TaskDispatchers } from './state/task.dispatchers';
import { CommonModule } from '@angular/common';
import { SharedCommonModule } from '../../shared/shared-common.module';
import { SharedLibsModule } from '../../shared/shared-libs.module';
import { TaskListComponent } from './task-list/task-list.component';
import { TaskFormComponent } from './task-form/task-form.component';
import { AddActivityDialogComponent } from './add-activity-dialog/add-activity-dialog.component';
import { reducerActivity } from '../activity/state/activity.reducer';
import { ActivitySelectors } from '../activity/state/activity.selectors';
import { ActivityDispatchers } from '../activity/state/activity.dispatchers';

@NgModule({
    declarations: [TaskListComponent, TaskFormComponent, AddActivityDialogComponent],
    imports: [
        CommonModule,
        SharedCommonModule,
        SharedCommonModule,
        SharedLibsModule,
        StoreModule.forRoot({}),
        StoreModule.forFeature('task', reducerTask),
        StoreModule.forFeature('activity', reducerActivity)
    ],
    exports: [],
    providers: [TaskSelectors, TaskDispatchers, ActivitySelectors, ActivityDispatchers],
    entryComponents: [AddActivityDialogComponent],
    schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
})
export class TaskModule {
    constructor() {

    }
}
