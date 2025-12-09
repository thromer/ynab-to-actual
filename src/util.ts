export function groupBy<T, K extends keyof T>(data: T[], field: K) {
  const res = new Map<T[K], T[]>();
  for (const item of data) {
    const key = item[field];
    const existing = res.get(key) || [];
    res.set(key, existing.concat([item]));
  }
  return res;
}

export function sortByKey<T>(arr: T[], key: keyof T): T[] {
  return [...arr].sort((item1, item2) => {
    if (item1[key] < item2[key]) {
      return -1;
    } else if (item1[key] > item2[key]) {
      return 1;
    }
    return 0;
  });
}
