/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

const STORAGE_KEY = 'GGRC_IT_Log';

class Storage {
  constructor() {
    let log = this.readLog();

    if (!log) {
      this.reset();
    }
  }

  add(item) {
    let log = this.readLog();

    log.push(item);

    localStorage.setItem(STORAGE_KEY, JSON.stringify(log));
  }
  readLog() {
    let storage = localStorage.getItem(STORAGE_KEY);

    return storage ? JSON.parse(storage) : null;
  }
  reset() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
  }
}

export default new Storage();
