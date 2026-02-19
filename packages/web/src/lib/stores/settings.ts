import { writable } from 'svelte/store';

export const algorithm = writable('bcrypt_cost12');
export const hardwareTier = writable('consumer');
