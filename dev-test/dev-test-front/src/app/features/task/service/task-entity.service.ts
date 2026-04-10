import { Injectable } from '@angular/core';
import { EntityCollectionServiceBase, EntityCollectionServiceElementsFactory } from '@ngrx/data';
import { HttpParams } from '@angular/common/http';
import { Task } from '../model/task';

@Injectable({ providedIn: 'root' })
export class TaskEntityService extends EntityCollectionServiceBase<Task> {

  constructor(serviceElementsFactory: EntityCollectionServiceElementsFactory) {
    super('Task', serviceElementsFactory);
  }
  
}
