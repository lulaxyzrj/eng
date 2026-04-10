import {Injectable} from '@angular/core';
import {Store} from '@ngrx/store';
import {EntityCache} from '@ngrx/data';
import {TaskEntityService} from './task-entity.service';
import {TaskSelectors} from '../state/task.selectors';
import { ApiService } from '../../../shared/service/api.service';
import { ToastService } from '../../../shared/service/toast.service';

@Injectable({providedIn: 'root'})
export class TaskService {

    allTasks$ = this.store.select(this.selectors.allTask).pipe();

    constructor(
        private store: Store<EntityCache>,
        private selectors: TaskSelectors,
        private toast: ToastService,
        private taskEntityService: TaskEntityService,
        private apiService: ApiService
    ) {
    }

    getAll() {
        return this.taskEntityService.getAll();
    }

    save(entity: any) {
        if (entity.id) {
            return this.taskEntityService.update(entity);
        }
        else {
            return this.taskEntityService.add(entity);
        }
    }

    getById(id: number) {
        return this.taskEntityService.getByKey(id);
    }

    inactivate(id: number) {
        this.apiService.inactivate(id).subscribe(
            data => {
                if (data) {
                    this.taskEntityService.updateOneInCache(data);
                }
            },
            err => {
                this.toast.showError(err.message);
            }
        );
    }

    reactivate(id: number) {
        this.apiService.reactivate(id).subscribe(
            data => {
                if (data) {
                    this.taskEntityService.updateOneInCache(data);
                }
            },
            err => {
                this.toast.showError(err.message);
            }
        );
    }

}
