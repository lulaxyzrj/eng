import {Injectable} from '@angular/core';
import {Store} from '@ngrx/store';
import {EntityCache} from '@ngrx/data';
import { ActivityDispatchers } from '../state/activity.dispatchers';
import { ActivityEntityService } from './activity-entity.service';
import { of } from 'rxjs';
import { TaskSelectors } from '../../task/state/task.selectors';

@Injectable({providedIn: 'root'})
export class ActivityService {

    allActivities$ = this.store.select(this.selectors.allTask).pipe();

    constructor(
        private store: Store<EntityCache>,
        private selectors: TaskSelectors,
        private activityDispatchers: ActivityDispatchers,
        private activityEntityService: ActivityEntityService
    ) {
    }

    getAll() {
        //return this.activityEntityService.getAll();
        return of([]);
    }

    save(entity: any) {

    }

    getById(id: number) {

    }

}
