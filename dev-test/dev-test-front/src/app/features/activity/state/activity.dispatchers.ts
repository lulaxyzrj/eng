import {Injectable} from '@angular/core';
import {Store} from '@ngrx/store';
import {State} from './activity.reducer';
import {SelectActivity, SetFilter} from './activity.actions';
import { FilterActivity } from '../../activity/model/activity-filterdata';
import { Activity } from '../../activity/model/activity';

@Injectable()
export class ActivityDispatchers {
    constructor(private store: Store<State>) {
    }

    setFilter(filterActivity: FilterActivity) {
        this.store.dispatch(SetFilter({filterActivity}));
    }

    selectActivity(activity: Activity) {
        this.store.dispatch(SelectActivity({activity}));
    }

}
