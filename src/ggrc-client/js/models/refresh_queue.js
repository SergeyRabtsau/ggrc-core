/*
 Copyright (C) 2018 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Mappings from './mappers/mappings';
import * as businessModels from './business-models';
import * as serviceModels from './service-models';
import * as mappingModels from './mapping-models';

const allModels = Object.assign({},
  businessModels,
  serviceModels,
  mappingModels
);

/*  RefreshQueue
 *
 *  enqueue(objs, force=false) -> queue or null
 *  trigger() -> Deferred
 */

const ModelRefreshQueue = can.Construct({}, {
  init: function (model) {
    this.model = model;
    this.ids = [];
    this.deferred = new $.Deferred();
    this.triggered = false;
    this.completed = false;
    this.updated_at = Date.now();
  },
  enqueue: function (id) {
    if (this.triggered) {
      return null;
    }
    if (this.ids.indexOf(id) === -1) {
      this.ids.push(id);
      this.updated_at = Date.now();
    }
    return this;
  },
  trigger: function () {
    let self = this;
    if (!this.triggered) {
      this.triggered = true;
      if (this.ids.length && this.model) {
        this.model.findAll({id__in: this.ids.join(',')}).then(function () {
          self.completed = true;
          self.deferred.resolve();
        }, function () {
          self.deferred.reject(...arguments);
        });
      } else {
        this.completed = true;
        this.deferred.resolve();
      }
    }
    return this.deferred;
  },
  trigger_with_debounce: function (delay, manager) {
    let msToWait = (delay || 0) + this.updated_at - Date.now();

    if (!this.triggered) {
      if (msToWait < 0 &&
        (!manager || manager.triggered_queues().length < 6)) {
        this.trigger();
      } else {
        setTimeout(
          this.proxy('trigger_with_debounce', delay, manager), msToWait);
      }
    }

    return this.deferred;
  },
});

const RefreshQueueManager = can.Construct({}, {
  init: function () {
    this.null_queue = new ModelRefreshQueue(null);
    this.queues = [];
  },
  triggered_queues: function () {
    return can.map(this.queues, function (queue) {
      if (queue.triggered) {
        return queue;
      }
    });
  },
  enqueue: function (obj, force) {
    let self = this;
    let model = obj.constructor;
    let modelName = model.shortName;
    let foundQueue = null;
    let id = obj.id;

    if (!obj.selfLink) {
      if (obj instanceof can.Model) {
        modelName = obj.constructor.shortName;
      } else if (obj.type) {
        // FIXME: obj.kind is to catch invalid stubs coming from Directives
        modelName = obj.type || obj.kind;
      }
    }
    model = allModels[modelName];

    if (!force) {
      // Check if the ID is already contained in another queue
      can.each(this.queues, function (queue) {
        if (!foundQueue &&
          queue.model === model && queue.ids.indexOf(id) > -1) {
          foundQueue = queue;
        }
      });
    }

    if (!foundQueue) {
      can.each(this.queues, function (queue) {
        if (!foundQueue &&
          queue.model === model &&
          !queue.triggered && queue.ids.length < 150) {
          foundQueue = queue.enqueue(id);
          return false;
        }
      });
      if (!foundQueue) {
        foundQueue = new ModelRefreshQueue(model);
        this.queues.push(foundQueue);
        foundQueue.enqueue(id);
        foundQueue.deferred.done(function () {
          let index = self.queues.indexOf(foundQueue);
          if (index > -1) {
            self.queues.splice(index, 1);
          }
        });
      }
    }

    return foundQueue;
  },
});

const RefreshQueue = can.Construct({
  refresh_queue_manager: new RefreshQueueManager(),
  refresh_all: function (instance, props, force) {
    let dfd = new can.Deferred();

    refreshAll(instance, props, dfd);
    return dfd;

    // Helper function called recursively for each property
    function refreshAll(instance, props, dfd) {
      let prop = props[0];
      let nextProps = props.slice(1);
      let next = instance[prop];
      let refreshQueue = new RefreshQueue();
      let dfds = [];
      let deferred;
      let hasBinding;

      if (next) {
        refreshQueue.enqueue(next, force);
        deferred = refreshQueue.trigger();
      } else if (instance.get_binding) {
        next = Mappings.get_binding(prop, instance);
        hasBinding = Mappings.has_binding(prop, instance);

        if (!hasBinding) {
          dfd.reject({
            message: prop + ' binding not found',
          });
        }
        if (hasBinding && next) {
          deferred = next.refresh_instances(force);
        }
      }
      if (deferred) {
        deferred.then(function (refreshedItems) {
          if (nextProps.length) {
            can.each(refreshedItems, function (item) {
              let df = new can.Deferred();
              refreshAll(item, nextProps, df);
              dfds.push(df);
            });
            // Resolve the original deferred only when all list deferreds
            //   have been resolved
            $.when(...dfds).then(function (items) {
              dfd.resolve(items);
            }, function () {
              dfd.reject.apply(this, arguments);
            });
            return;
          }
          // All items were refreshed, resolve the deferred
          if (next.push || next.list) {
            // Last refreshed property was a list
            dfd.resolve(refreshedItems);
          }
          // Last refreshed property was a single instance, return it as such
          dfd.resolve(refreshedItems[0]);
        }, function () {
          dfd.reject.apply(this, arguments);
        });
      } else {
        console.warn('refresh_all failed at', prop);
      }
    }
  },
}, {
  init: function () {
    this.objects = [];
    this.queues = [];
    this.deferred = new $.Deferred();
    this.triggered = false;
    this.completed = false;

    return this;
  },
  enqueue: function (objs, force) {
    let queue;
    if (!objs) {
      return;
    }
    if (this.triggered) {
      return null;
    }
    if (objs.push) {
      can.each(objs, function (obj) {
        this.enqueue(obj, force);
      }, this);
      return this;
    }

    this.objects.push(objs);
    if (force || !objs.selfLink) {
      queue = this.constructor.refresh_queue_manager.enqueue(objs, force);
      if (this.queues.indexOf(queue) === -1) {
        this.queues.push(queue);
      }
    }
    return this;
  },
  trigger: function (delay) {
    let self = this;
    let deferreds = [];

    if (!delay) {
      delay = 150;
    }

    this.triggered = true;
    can.each(this.queues, function (queue) {
      deferreds.push(
        queue.trigger_with_debounce(delay,
          self.constructor.refresh_queue_manager));
    });

    if (deferreds.length) {
      $.when(...deferreds).then(function () {
        self.deferred.resolve(can.map(self.objects, function (obj) {
          return obj.reify();
        }));
      }, function () {
        self.deferred.reject(...arguments);
      });
    } else {
      return this.deferred.resolve(this.objects);
    }

    return this.deferred;
  },
});

export default RefreshQueue;
