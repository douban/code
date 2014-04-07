define([], () ->
  class App
    _cache: {}
    origin: location.origin

  return () ->
    return new App()
)
