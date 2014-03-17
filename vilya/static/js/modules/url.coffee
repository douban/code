define([], () ->
    exports = {}

    exports.getURLParameter = (name, search) ->
        search = search || location.search || location.hash
        param = search.match(RegExp(name + '=' + '(.+?)(&|$)'))
        if param
            return decodeURIComponent(param[1])
        else
            return undefined

    rNonQuerystring = /\+/g

    exports.deparam = (string) ->
        params = {}
        paramsArray = string.replace(rNonQuerystring, ' ').split('&')

        for paramString in paramsArray
            pair = paramString.split('=')
            paramName = decodeURIComponent([pair[0]])
            paramValue = decodeURIComponent([pair[1]])
            params[paramName] = paramValue

        return params

    # copy from
    # https://github.com/jfromaniello/url-join/blob/master/lib/url-join.js
    # version: b02169596877a1e6cd518f1b0d711f38c721fb02
    normalize = (str) ->
        return str.replace(/[\/]+/g, '/').replace(/\/\?/g, '?').replace(/\/\#/g, '#').replace(/\:\//g, '://')

    join = exports.join = () ->
        joined = [].slice.call(arguments, 0).join('/')
        return normalize(joined)

    exports.addParam = (url, params) ->
        paramString = ''

        for key of params
            if (!params.hasOwnProperty(key))
                continue

            value = params[key]
            if (value == '' || typeof value == 'undefined')
                continue

            if (paramString)
                paramString += '&'
            paramString += encodeURIComponent(key) + '=' + encodeURIComponent(value)

        if (!paramString)
            return url

        hash = ''
        search = ''
        rest = url
        hashIndex = rest.indexOf('#')
        markIndex = rest.indexOf('?')

        if (hashIndex != -1)
            hash = rest.substr(hashIndex)
            rest = rest.slice(0, hashIndex)

        if (markIndex != -1)
            search = rest.substr(markIndex)
            rest = rest.slice(0, markIndex)

        return (rest + ((search + '&' + paramString) if search else ('?' + paramString)) + (hash ? hash : ''))

    hasSameOrigin = exports.hasSameOrigin = (url, originUrl) ->
        if (url[0] == '/')
            return true
        rOrigin = new RegExp('^' + originUrl)
        return rOrigin.test(url)

    exports.getRelativeUrl = (url, originUrl) ->
        if (url[0] == '/' || !hasSameOrigin(url, originUrl))
            return url
        return join('/', url.substr(originUrl.length))

    return exports
)
