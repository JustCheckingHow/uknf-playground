import type { StylesConfig } from 'react-select';

export interface SelectOption {
  value: string;
  label: string;
}

const baseSelectStyles: StylesConfig<SelectOption, false> = {
  control: (base, state) => ({
    ...base,
    borderRadius: 6,
    borderColor: state.isFocused ? '#2563eb' : '#cbd5f5',
    boxShadow: state.isFocused ? '0 0 0 1px #2563eb' : 'none',
    '&:hover': {
      borderColor: state.isFocused ? '#2563eb' : '#cbd5f5'
    },
    minHeight: '38px'
  }),
  valueContainer: (base) => ({
    ...base,
    padding: '2px 8px'
  }),
  singleValue: (base) => ({
    ...base,
    fontSize: '0.875rem'
  }),
  placeholder: (base) => ({
    ...base,
    fontSize: '0.875rem',
    color: '#94a3b8'
  }),
  input: (base) => ({
    ...base,
    fontSize: '0.875rem'
  }),
  dropdownIndicator: (base, state) => ({
    ...base,
    color: state.isFocused ? '#2563eb' : '#94a3b8',
    padding: '4px'
  }),
  clearIndicator: (base) => ({
    ...base,
    padding: '4px'
  }),
  menu: (base) => ({
    ...base,
    borderRadius: 6,
    overflow: 'hidden'
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected ? '#2563eb' : state.isFocused ? '#e2e8f0' : 'transparent',
    color: state.isSelected ? '#ffffff' : '#0f172a',
    cursor: 'pointer',
    fontSize: '0.875rem'
  })
};

export const select2Styles = baseSelectStyles;
