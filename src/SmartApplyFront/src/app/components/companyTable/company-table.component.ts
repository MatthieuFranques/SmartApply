import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Company } from '../../models/company.model';

@Component({
  selector: 'app-company-table',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './company-table.component.html',
  styleUrls: ['./company-table.component.scss'],
})
export class CompanyTableComponent {
  @Input() companies: Company[] = [];
  @Output() rowClick = new EventEmitter<Company>();
}
