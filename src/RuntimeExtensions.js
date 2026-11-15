(function (global) {
  "use strict";

  const runtimeConstructor = global.Runtime;
  if (typeof runtimeConstructor !== "function") {
    throw new Error("No se encontró el constructor del runtime de Clickteam.");
  }

  const listeners = new Map();
  const extensions = new Map();
  let status = "idle";
  let runtimeInstance = null;

  function dispatch(eventName, detail) {
    const callbacks = listeners.get(eventName);
    if (callbacks) {
      callbacks.forEach(function (callback) {
        try {
          callback(detail);
        } catch (error) {
          console.error("Error en un callback del runtime:", error);
        }
      });
    }
    global.dispatchEvent(new CustomEvent("fnaf3:runtime:" + eventName, {
      detail: detail
    }));
  }

  function initializeExtension(id, initialize) {
    try {
      initialize({
        runtime: runtimeInstance,
        game: global.FNAF3 && global.FNAF3.api,
        canvas: global.document.getElementById("MMFCanvas")
      });
      dispatch("extension.loaded", { id: id });
    } catch (error) {
      dispatch("extension.error", {
        id: id,
        message: String(error && error.message || error)
      });
      console.error("No se pudo iniciar la extensión del runtime " + id + ":", error);
    }
  }

  global.FNAF3Runtime = {
    version: "1.0.0",
    getStatus: function () {
      return status;
    },
    getCanvas: function () {
      return global.document.getElementById("MMFCanvas");
    },
    getInstance: function () {
      return runtimeInstance;
    },
    registerExtension: function (id, initialize) {
      if (typeof id !== "string" || !/^[a-z0-9][a-z0-9_-]*$/.test(id)) {
        throw new TypeError("La extensión requiere un id válido.");
      }
      if (typeof initialize !== "function") {
        throw new TypeError("La extensión requiere una función de inicialización.");
      }
      if (extensions.has(id)) {
        throw new Error("La extensión " + id + " ya está registrada.");
      }
      extensions.set(id, initialize);
      if (runtimeInstance) {
        initializeExtension(id, initialize);
      }
      return function () {
        extensions.delete(id);
      };
    },
    on: function (eventName, callback) {
      if (typeof eventName !== "string" || typeof callback !== "function") {
        throw new TypeError("on requiere el nombre del evento y una función.");
      }
      if (!listeners.has(eventName)) {
        listeners.set(eventName, new Set());
      }
      listeners.get(eventName).add(callback);
      return function () {
        listeners.get(eventName).delete(callback);
      };
    }
  };

  global.Runtime = new Proxy(runtimeConstructor, {
    construct: function (target, args, newTarget) {
      status = "starting";
      dispatch("starting", { canvasId: args[0] });
      try {
        const instance = Reflect.construct(target, args, newTarget);
        runtimeInstance = instance;
        status = "running";
        dispatch("created", { canvasId: args[0] });
        extensions.forEach(function (initialize, id) {
          initializeExtension(id, initialize);
        });
        return instance;
      } catch (error) {
        status = "error";
        runtimeInstance = null;
        dispatch("error", {
          canvasId: args[0],
          message: String(error && error.message || error)
        });
        throw error;
      }
    }
  });
})(window);
