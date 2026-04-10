import { Injectable, Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'labelPipe',
})
@Injectable()
export class LabelPipe implements PipeTransform {
  transform(items: any[], param: string): any {
    param = param.toLowerCase();

    if (items) {
      return items.filter((item, index) => {
        const find = item.value.toLowerCase().indexOf(param);
        return find === -1 ? false : true;
      });
    }
  }
}
