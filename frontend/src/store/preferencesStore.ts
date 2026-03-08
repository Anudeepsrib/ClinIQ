import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PreferencesState {
    layoutMode: 'standard' | 'enterprise';
    toggleLayoutMode: () => void;
}

export const usePreferencesStore = create<PreferencesState>()(
    persist(
        (set) => ({
            layoutMode: 'enterprise', // Default to strict 80/20 grid per user request
            toggleLayoutMode: () =>
                set((state) => ({
                    layoutMode: state.layoutMode === 'standard' ? 'enterprise' : 'standard',
                })),
        }),
        {
            name: 'cliniq-preferences',
        }
    )
);
