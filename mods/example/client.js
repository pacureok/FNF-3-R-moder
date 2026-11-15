(function () {
  "use strict";

  window.FNAF3Runtime.registerExtension("example", function (context) {
    console.info(
      "[FNAF3 mod example] Runtime extension connected.",
      context.canvas,
      context.runtime
    );
    context.game.on("night.start", function (configuration) {
      console.info("[FNAF3 mod example] Custom Night configuration:", configuration);
    });
  });
})();
