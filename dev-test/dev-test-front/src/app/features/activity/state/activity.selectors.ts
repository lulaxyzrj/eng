import {Injectable} from '@angular/core';
import {createFeatureSelector, createSelector} from '@ngrx/store';
import {initialState, State} from './activity.reducer';
import { Activity } from '../../activity/model/activity';
import { ActivityEntityService } from '../service/activity-entity.service';

const getActivityState = createFeatureSelector<State>('Activity');

@Injectable()
export class ActivitySelectors {

    selectFilter = createSelector(
        getActivityState, (state: State) => state ? state.filterActivity : initialState.filterActivity);

    allActivities = createSelector(
        this.activityEntityService.selectors.selectEntities,
        activities => {
            return activities;
        }
    );

    selectActivity = createSelector(
        this.selectFilter,
        this.activityEntityService.selectors.selectEntityMap,
        (filterData, activity) => filterData ? activity[filterData.id] : {} as Activity
    );

    constructor(
        private activityEntityService: ActivityEntityService) {
    }

}
