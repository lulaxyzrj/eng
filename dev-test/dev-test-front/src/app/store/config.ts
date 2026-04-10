import { DefaultDataServiceConfig } from '@ngrx/data';

const root = '/api';

export const defaultDataServiceConfig: DefaultDataServiceConfig = {
    root,

    entityHttpResourceUrls: {
        Task: {
            entityResourceUrl: `${root}/tasks/`,
            collectionResourceUrl: `${root}/tasks/`
        },
        Activity: {
            entityResourceUrl: `${root}/activities/`,
            collectionResourceUrl: `${root}/activities/`
        }
    }
};
