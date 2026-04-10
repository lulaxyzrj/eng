import { Injectable } from '@angular/core';
import { EntityCollectionServiceBase, EntityCollectionServiceElementsFactory } from '@ngrx/data';
import { Activity } from '../../activity/model/activity';

@Injectable({ providedIn: 'root' })
export class ActivityEntityService extends EntityCollectionServiceBase<Activity> {

  constructor(serviceElementsFactory: EntityCollectionServiceElementsFactory) {
    super('Activity', serviceElementsFactory);
  }

}
