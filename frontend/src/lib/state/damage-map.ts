import { atom } from 'jotai';

export const damageSourceState = atom<'all' | string[]>('all');
export const damageTypeState = atom('direct');
export const damageProtectionStandardState = atom(0);
