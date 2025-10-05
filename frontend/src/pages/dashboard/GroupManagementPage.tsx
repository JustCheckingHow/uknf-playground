'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Select, { type MultiValue, type StylesConfig } from 'react-select';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import type { User, UserGroup, UserType } from '@/types';
import { select2Styles, type SelectOption } from '@/components/ui/select2Styles';
import { USER_TYPE_LABELS, USER_TYPE_SELECT_OPTIONS } from '@/lib/userTypes';

type GroupPayload = {
  name: string;
  user_ids: number[];
};

type UpdateGroupVariables = {
  groupId: number;
  payload: Partial<GroupPayload>;
  successMessage: string;
};

type DeleteGroupVariables = {
  groupId: number;
  groupName: string;
};

export default function GroupManagementPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [searchInput, setSearchInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [userTypeFilter, setUserTypeFilter] = useState<'all' | UserType>('all');
  const [selectedUsers, setSelectedUsers] = useState<Set<number>>(new Set());
  const [isCreateModeVisible, setIsCreateModeVisible] = useState(false);
  const [groupName, setGroupName] = useState('');
  const [pendingAddMembers, setPendingAddMembers] = useState<Record<number, string[]>>({});
  const multiSelectStyles = select2Styles as unknown as StylesConfig<SelectOption, true>;

  const userTypeOptions = useMemo<SelectOption[]>(
    () => [{ value: 'all', label: 'Wszyscy' }, ...USER_TYPE_SELECT_OPTIONS],
    []
  );

  useEffect(() => {
    const handle = window.setTimeout(() => setSearchTerm(searchInput.trim()), 300);
    return () => window.clearTimeout(handle);
  }, [searchInput]);

  const usersQuery = useQuery({
    queryKey: ['group-users', { searchTerm, userTypeFilter }],
    enabled: user?.role === 'system_admin',
    queryFn: async () => {
      const params: Record<string, string> = { non_admin: 'true' };
      if (searchTerm) {
        params.search = searchTerm;
      }
      if (userTypeFilter !== 'all') {
        params.user_type = userTypeFilter;
      }
      const response = await apiClient.get<User[]>('/auth/users/', { params });
      return response.data;
    }
  });

  const groupsQuery = useQuery({
    queryKey: ['user-groups'],
    enabled: user?.role === 'system_admin',
    queryFn: async () => {
      const response = await apiClient.get<UserGroup[]>('/auth/user-groups/');
      return response.data;
    }
  });

  const createGroupMutation = useMutation({
    mutationFn: async (payload: GroupPayload) => {
      await apiClient.post('/auth/user-groups/', payload);
    },
    onSuccess: () => {
      toast.success('Grupa została utworzona.');
      setSelectedUsers(new Set());
      setGroupName('');
      setIsCreateModeVisible(false);
      queryClient.invalidateQueries({ queryKey: ['group-users'] });
      queryClient.invalidateQueries({ queryKey: ['user-groups'] });
    },
    onError: () => {
      toast.error('Nie udało się utworzyć grupy. Spróbuj ponownie później.');
    }
  });

  const updateGroupMutation = useMutation({
    mutationFn: async ({ groupId, payload }: UpdateGroupVariables) => {
      await apiClient.patch(`/auth/user-groups/${groupId}/`, payload);
    },
    onSuccess: (_, variables) => {
      toast.success(variables.successMessage);
      setPendingAddMembers((prev) => ({ ...prev, [variables.groupId]: [] }));
      queryClient.invalidateQueries({ queryKey: ['user-groups'] });
      queryClient.invalidateQueries({ queryKey: ['group-users'] });
    },
    onError: () => {
      toast.error('Nie udało się zaktualizować grupy. Spróbuj ponownie później.');
    }
  });

  const deleteGroupMutation = useMutation({
    mutationFn: async ({ groupId }: DeleteGroupVariables) => {
      await apiClient.delete(`/auth/user-groups/${groupId}/`);
    },
    onSuccess: (_, variables) => {
      toast.success(`Grupa "${variables.groupName}" została usunięta.`);
      setPendingAddMembers((prev) => {
        const next = { ...prev };
        delete next[variables.groupId];
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['user-groups'] });
      queryClient.invalidateQueries({ queryKey: ['group-users'] });
    },
    onError: () => {
      toast.error('Nie udało się usunąć grupy. Spróbuj ponownie później.');
    }
  });

  const isLoading = usersQuery.isLoading;
  const users = usersQuery.data ?? [];
  const groups = groupsQuery.data ?? [];

  const allVisibleSelected = useMemo(() => {
    if (!users.length) {
      return false;
    }
    return users.every((item) => selectedUsers.has(item.id));
  }, [selectedUsers, users]);

  const toggleUserSelection = (userId: number) => {
    setSelectedUsers((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelectedUsers((prev) => {
      if (allVisibleSelected) {
        const next = new Set(prev);
        users.forEach((item) => next.delete(item.id));
        return next;
      }
      const next = new Set(prev);
      users.forEach((item) => next.add(item.id));
      return next;
    });
  };

  const startCreateGroup = () => {
    if (!selectedUsers.size) {
      toast.info('Wybierz co najmniej jednego użytkownika, aby utworzyć grupę.');
      return;
    }
    setIsCreateModeVisible(true);
  };

  const submitGroup = () => {
    if (!groupName.trim()) {
      toast.info('Podaj nazwę nowej grupy.');
      return;
    }
    createGroupMutation.mutate({ name: groupName.trim(), user_ids: Array.from(selectedUsers) });
  };

  const handleRemoveMember = async (group: UserGroup, userId: number) => {
    const remaining = group.users.map((member) => member.id).filter((id) => id !== userId);
    if (remaining.length === group.users.length) {
      return;
    }
    try {
      await updateGroupMutation.mutateAsync({
        groupId: group.id,
        payload: { user_ids: remaining },
        successMessage: 'Zapisano zmiany w grupie.'
      });
    } catch {
      /* already handled in onError */
    }
  };

  const handleAddMembers = async (group: UserGroup) => {
    const selected = pendingAddMembers[group.id] ?? [];
    if (!selected.length) {
      toast.info('Wybierz użytkowników, których chcesz dodać do grupy.');
      return;
    }
    const currentMemberIds = new Set(group.users.map((member) => member.id));
    selected.forEach((value) => currentMemberIds.add(Number(value)));
    try {
      await updateGroupMutation.mutateAsync({
        groupId: group.id,
        payload: { user_ids: Array.from(currentMemberIds) },
        successMessage: 'Nowi użytkownicy zostali dodani do grupy.'
      });
    } catch {
      /* already handled in onError */
    }
  };

  const handleDeleteGroup = (group: UserGroup) => {
    if (!window.confirm(`Czy na pewno chcesz usunąć grupę "${group.name}"?`)) {
      return;
    }
    deleteGroupMutation.mutate({ groupId: group.id, groupName: group.name });
  };

  if (user?.role !== 'system_admin') {
    return (
      <Card className="text-sm text-slate-600">
        Dostęp do modułu zarządzania grupami jest ograniczony do administratorów systemu.
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="space-y-2">
        <h1 className="text-lg font-semibold text-slate-900">Zarządzanie grupami użytkowników</h1>
        <p className="text-sm text-slate-600">
          Grupuj użytkowników zewnętrznych, aby szybciej delegować zadania lub udostępniać zasoby. Wybierz osoby z listy,
          a następnie utwórz dla nich nową grupę.
        </p>
      </Card>

      <Card className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end">
          <label className="flex-1 text-sm">
            <span className="text-slate-700">Nazwa lub e-mail</span>
            <input
              type="text"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Wyszukaj użytkownika"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
            />
          </label>
          <div className="w-full text-sm md:w-60">
            <label htmlFor="group-user-type" className="block text-slate-700">
              Typ użytkownika
            </label>
            <Select<SelectOption>
              inputId="group-user-type"
              instanceId="group-user-type"
              className="mt-1 w-full"
              classNamePrefix="select2"
              options={userTypeOptions}
              value={userTypeOptions.find((option) => option.value === userTypeFilter) ?? null}
              isClearable
              isSearchable
              styles={select2Styles}
              noOptionsMessage={() => 'Brak wyników'}
              onChange={(option) => setUserTypeFilter((option?.value as 'all' | UserType) ?? 'all')}
            />
          </div>
          <Button variant="outline" onClick={() => usersQuery.refetch()} isLoading={usersQuery.isFetching}>
            Odśwież listę
          </Button>
        </div>

        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allVisibleSelected}
                    onChange={toggleSelectAll}
                    aria-label="Zaznacz wszystkich widocznych"
                  />
                </th>
                <th className="px-4 py-3">Użytkownik</th>
                <th className="px-4 py-3">Rola</th>
                <th className="px-4 py-3">Typ użytkownika</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-500">
                    Ładowanie listy użytkowników...
                  </td>
                </tr>
              )}
              {usersQuery.isError && !isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-sm text-red-500">
                    Nie udało się pobrać listy użytkowników.
                  </td>
                </tr>
              )}
              {!isLoading && users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-500">
                    Brak użytkowników spełniających kryteria wyszukiwania.
                  </td>
                </tr>
              )}
              {!isLoading &&
                users.map((item) => (
                  <tr key={item.id} className="hover:bg-primary/5">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedUsers.has(item.id)}
                        onChange={() => toggleUserSelection(item.id)}
                        aria-label={`Zaznacz użytkownika ${item.email}`}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-medium text-slate-900">
                          {item.first_name || item.last_name ? `${item.first_name} ${item.last_name}`.trim() : item.email}
                        </span>
                        <span className="text-xs text-slate-500">{item.email}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{item.role_display}</td>
                    <td className="px-4 py-3">
                      <Badge tone="info">{USER_TYPE_LABELS[item.user_type]}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={item.is_active ? 'success' : 'warning'}>
                        {item.is_active ? 'Aktywny' : 'Nieaktywny'}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-600">
            Wybrano {selectedUsers.size}{' '}
            {selectedUsers.size === 1 ? 'użytkownika' : 'użytkowników'}.
          </p>
          <div className="flex flex-wrap gap-2">
            {isCreateModeVisible ? (
              <>
                <input
                  type="text"
                  value={groupName}
                  onChange={(event) => setGroupName(event.target.value)}
                  placeholder="Nazwa grupy"
                  className="w-64 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                />
                <Button onClick={submitGroup} isLoading={createGroupMutation.isPending}>
                  Utwórz grupę
                </Button>
                <Button variant="ghost" onClick={() => setIsCreateModeVisible(false)} disabled={createGroupMutation.isPending}>
                  Anuluj
                </Button>
              </>
            ) : (
              <Button onClick={startCreateGroup} disabled={!selectedUsers.size}>
                Utwórz grupę z zaznaczonych
              </Button>
            )}
          </div>
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Istniejące grupy</h2>
            <p className="text-sm text-slate-600">Lista grup dostępnych w systemie oraz ich aktualni członkowie.</p>
          </div>
          <Button variant="outline" onClick={() => groupsQuery.refetch()} isLoading={groupsQuery.isFetching}>
            Odśwież
          </Button>
        </div>
        {groupsQuery.isLoading ? (
          <p className="text-sm text-slate-500">Ładowanie grup...</p>
        ) : groupsQuery.isError ? (
          <p className="text-sm text-red-500">Nie udało się pobrać listy grup.</p>
        ) : groups.length === 0 ? (
          <p className="text-sm text-slate-500">Nie utworzono jeszcze żadnych grup.</p>
        ) : (
          <ul className="space-y-3">
            {groups.map((group) => {
              const currentUpdatePending =
                updateGroupMutation.isPending && updateGroupMutation.variables?.groupId === group.id;
              const currentDeletePending =
                deleteGroupMutation.isPending && deleteGroupMutation.variables?.groupId === group.id;
              const plannedAdditions = pendingAddMembers[group.id] ?? [];
              const availableOptions: SelectOption[] = users
                .filter((candidate) => !group.users.some((member) => member.id === candidate.id))
                .map((candidate) => ({
                  value: String(candidate.id),
                  label:
                    candidate.first_name || candidate.last_name
                      ? `${candidate.first_name} ${candidate.last_name}`.trim()
                      : candidate.email
                }));
              const selectedOptions = plannedAdditions.reduce<SelectOption[]>((acc, value) => {
                const option = availableOptions.find((item) => item.value === value);
                if (option) {
                  acc.push(option);
                  return acc;
                }
                const fallbackUser = users.find((candidate) => String(candidate.id) === value);
                if (fallbackUser) {
                  acc.push({
                    value,
                    label:
                      fallbackUser.first_name || fallbackUser.last_name
                        ? `${fallbackUser.first_name} ${fallbackUser.last_name}`.trim()
                        : fallbackUser.email
                  });
                }
                return acc;
              }, []);

              return (
                <li key={group.id} className="rounded-lg border border-slate-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-base font-semibold text-slate-900">{group.name}</h3>
                      <p className="text-xs text-slate-500">{group.members_count} członków</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-500">
                        Utworzono: {new Date(group.created_at).toLocaleDateString('pl-PL')}
                      </span>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteGroup(group)} isLoading={currentDeletePending}>
                        Usuń grupę
                      </Button>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {group.users.length ? (
                      group.users.map((member) => (
                        <div key={member.id} className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs">
                          <span className="text-slate-700">
                            {member.first_name || member.last_name ? `${member.first_name} ${member.last_name}`.trim() : member.email}
                          </span>
                          <Button variant="ghost" size="sm" onClick={() => handleRemoveMember(group, member.id)} isLoading={currentUpdatePending}>
                            Usuń
                          </Button>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">Brak przypisanych członków.</span>
                    )}
                  </div>
                  <div className="mt-4 flex flex-col gap-2 md:flex-row md:items-center">
                    <div className="flex-1">
                      <Select<SelectOption, true>
                        className="w-full"
                        classNamePrefix="select2"
                        isMulti
                        isSearchable
                        placeholder="Dodaj użytkowników do grupy"
                        styles={multiSelectStyles}
                        noOptionsMessage={() => 'Brak użytkowników do dodania'}
                        options={availableOptions}
                        value={selectedOptions}
                        onChange={(options: MultiValue<SelectOption>) =>
                          setPendingAddMembers((prev) => ({
                            ...prev,
                            [group.id]: options.map((option) => option.value)
                          }))
                        }
                      />
                    </div>
                    <Button size="sm" onClick={() => handleAddMembers(group)} isLoading={currentUpdatePending}>
                      Dodaj do grupy
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
