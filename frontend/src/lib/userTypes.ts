import type { SelectOption } from '@/components/ui/select2Styles';
import type { UserType } from '@/types';

export const USER_TYPE_LABELS: Record<UserType, string> = {
  bank: 'Bank',
  fundusz_inwestycyjny: 'Fundusz inwestycyjny',
  inne: 'Inne'
};

export const USER_TYPE_SELECT_OPTIONS: SelectOption[] = [
  { value: 'bank', label: USER_TYPE_LABELS.bank },
  { value: 'fundusz_inwestycyjny', label: USER_TYPE_LABELS.fundusz_inwestycyjny },
  { value: 'inne', label: USER_TYPE_LABELS.inne }
];
