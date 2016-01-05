
require.config({ enable_ozma: true });


/* @source mod/team_header.js */;

define('mod/team_header', [
  "jquery"
], function($){
  $(function(){
     var JoinOrLeaveTeam = function (url, onSuccess) {
         $.post(url, function (ret) {
             if (ret.r === 0) {
                 onSuccess();
             }
         }, 'json');
     };
     $('.join-or-leave-btn').click(function () {
         var Btn = $(this), team = Btn.attr('data-team'), _type = Btn.attr('data-type'),
             url = '/hub/team/' + team + '/' + _type;
         if (_type === "leave") {
             JoinOrLeaveTeam(url, function () {
                 Btn.removeClass('btn-danger');
                 Btn.addClass('btn-success');
                 Btn.html('Join');
                 Btn.attr('data-type', 'join');
             }); 
         }else{
             JoinOrLeaveTeam(url, function () {
                 Btn.removeClass('btn-success');
                 Btn.addClass('btn-danger');
                 Btn.html('Leave');
                 Btn.attr('data-type', 'leave');
             }); 
         }
     });
  });
});

/* @source lib/tinycolor.js */;

// TinyColor v0.9.16
// https://github.com/bgrins/TinyColor
// 2013-08-10, Brian Grinstead, MIT License

(function() {

var trimLeft = /^[\s,#]+/,
    trimRight = /\s+$/,
    tinyCounter = 0,
    math = Math,
    mathRound = math.round,
    mathMin = math.min,
    mathMax = math.max,
    mathRandom = math.random;

function tinycolor (color, opts) {

    color = (color) ? color : '';
    opts = opts || { };

    // If input is already a tinycolor, return itself
    if (typeof color == "object" && color.hasOwnProperty("_tc_id")) {
       return color;
    }

    var rgb = inputToRGB(color);
    var r = rgb.r,
        g = rgb.g,
        b = rgb.b,
        a = rgb.a,
        roundA = mathRound(100*a) / 100,
        format = opts.format || rgb.format;

    // Don't let the range of [0,255] come back in [0,1].
    // Potentially lose a little bit of precision here, but will fix issues where
    // .5 gets interpreted as half of the total, instead of half of 1
    // If it was supposed to be 128, this was already taken care of by `inputToRgb`
    if (r < 1) { r = mathRound(r); }
    if (g < 1) { g = mathRound(g); }
    if (b < 1) { b = mathRound(b); }

    return {
        ok: rgb.ok,
        format: format,
        _tc_id: tinyCounter++,
        alpha: a,
        getAlpha: function() {
            return a;
        },
        setAlpha: function(value) {
            a = boundAlpha(value);
            roundA = mathRound(100*a) / 100;
        },
        toHsv: function() {
            var hsv = rgbToHsv(r, g, b);
            return { h: hsv.h * 360, s: hsv.s, v: hsv.v, a: a };
        },
        toHsvString: function() {
            var hsv = rgbToHsv(r, g, b);
            var h = mathRound(hsv.h * 360), s = mathRound(hsv.s * 100), v = mathRound(hsv.v * 100);
            return (a == 1) ?
              "hsv("  + h + ", " + s + "%, " + v + "%)" :
              "hsva(" + h + ", " + s + "%, " + v + "%, "+ roundA + ")";
        },
        toHsl: function() {
            var hsl = rgbToHsl(r, g, b);
            return { h: hsl.h * 360, s: hsl.s, l: hsl.l, a: a };
        },
        toHslString: function() {
            var hsl = rgbToHsl(r, g, b);
            var h = mathRound(hsl.h * 360), s = mathRound(hsl.s * 100), l = mathRound(hsl.l * 100);
            return (a == 1) ?
              "hsl("  + h + ", " + s + "%, " + l + "%)" :
              "hsla(" + h + ", " + s + "%, " + l + "%, "+ roundA + ")";
        },
        toHex: function(allow3Char) {
            return rgbToHex(r, g, b, allow3Char);
        },
        toHexString: function(allow3Char) {
            return '#' + this.toHex(allow3Char);
        },
        toHex8: function() {
            return rgbaToHex(r, g, b, a);
        },
        toHex8String: function() {
            return '#' + this.toHex8();
        },
        toRgb: function() {
            return { r: mathRound(r), g: mathRound(g), b: mathRound(b), a: a };
        },
        toRgbString: function() {
            return (a == 1) ?
              "rgb("  + mathRound(r) + ", " + mathRound(g) + ", " + mathRound(b) + ")" :
              "rgba(" + mathRound(r) + ", " + mathRound(g) + ", " + mathRound(b) + ", " + roundA + ")";
        },
        toPercentageRgb: function() {
            return { r: mathRound(bound01(r, 255) * 100) + "%", g: mathRound(bound01(g, 255) * 100) + "%", b: mathRound(bound01(b, 255) * 100) + "%", a: a };
        },
        toPercentageRgbString: function() {
            return (a == 1) ?
              "rgb("  + mathRound(bound01(r, 255) * 100) + "%, " + mathRound(bound01(g, 255) * 100) + "%, " + mathRound(bound01(b, 255) * 100) + "%)" :
              "rgba(" + mathRound(bound01(r, 255) * 100) + "%, " + mathRound(bound01(g, 255) * 100) + "%, " + mathRound(bound01(b, 255) * 100) + "%, " + roundA + ")";
        },
        toName: function() {
            if (a === 0) {
                return "transparent";
            }

            return hexNames[rgbToHex(r, g, b, true)] || false;
        },
        toFilter: function(secondColor) {
            var hex8String = '#' + rgbaToHex(r, g, b, a);
            var secondHex8String = hex8String;
            var gradientType = opts && opts.gradientType ? "GradientType = 1, " : "";

            if (secondColor) {
                var s = tinycolor(secondColor);
                secondHex8String = s.toHex8String();
            }

            return "progid:DXImageTransform.Microsoft.gradient("+gradientType+"startColorstr="+hex8String+",endColorstr="+secondHex8String+")";
        },
        toString: function(format) {
            var formatSet = !!format;
            format = format || this.format;

            var formattedString = false;
            var hasAlphaAndFormatNotSet = !formatSet && a < 1 && a > 0;
            var formatWithAlpha = hasAlphaAndFormatNotSet && (format === "hex" || format === "hex6" || format === "hex3" || format === "name");

            if (format === "rgb") {
                formattedString = this.toRgbString();
            }
            if (format === "prgb") {
                formattedString = this.toPercentageRgbString();
            }
            if (format === "hex" || format === "hex6") {
                formattedString = this.toHexString();
            }
            if (format === "hex3") {
                formattedString = this.toHexString(true);
            }
            if (format === "hex8") {
                formattedString = this.toHex8String();
            }
            if (format === "name") {
                formattedString = this.toName();
            }
            if (format === "hsl") {
                formattedString = this.toHslString();
            }
            if (format === "hsv") {
                formattedString = this.toHsvString();
            }

            if (formatWithAlpha) {
                return this.toRgbString();
            }

            return formattedString || this.toHexString();
        }
    };
}

// If input is an object, force 1 into "1.0" to handle ratios properly
// String input requires "1.0" as input, so 1 will be treated as 1
tinycolor.fromRatio = function(color, opts) {
    if (typeof color == "object") {
        var newColor = {};
        for (var i in color) {
            if (color.hasOwnProperty(i)) {
                if (i === "a") {
                    newColor[i] = color[i];
                }
                else {
                    newColor[i] = convertToPercentage(color[i]);
                }
            }
        }
        color = newColor;
    }

    return tinycolor(color, opts);
};

// Given a string or object, convert that input to RGB
// Possible string inputs:
//
//     "red"
//     "#f00" or "f00"
//     "#ff0000" or "ff0000"
//     "#ff000000" or "ff000000"
//     "rgb 255 0 0" or "rgb (255, 0, 0)"
//     "rgb 1.0 0 0" or "rgb (1, 0, 0)"
//     "rgba (255, 0, 0, 1)" or "rgba 255, 0, 0, 1"
//     "rgba (1.0, 0, 0, 1)" or "rgba 1.0, 0, 0, 1"
//     "hsl(0, 100%, 50%)" or "hsl 0 100% 50%"
//     "hsla(0, 100%, 50%, 1)" or "hsla 0 100% 50%, 1"
//     "hsv(0, 100%, 100%)" or "hsv 0 100% 100%"
//
function inputToRGB(color) {

    var rgb = { r: 0, g: 0, b: 0 };
    var a = 1;
    var ok = false;
    var format = false;

    if (typeof color == "string") {
        color = stringInputToObject(color);
    }

    if (typeof color == "object") {
        if (color.hasOwnProperty("r") && color.hasOwnProperty("g") && color.hasOwnProperty("b")) {
            rgb = rgbToRgb(color.r, color.g, color.b);
            ok = true;
            format = String(color.r).substr(-1) === "%" ? "prgb" : "rgb";
        }
        else if (color.hasOwnProperty("h") && color.hasOwnProperty("s") && color.hasOwnProperty("v")) {
            color.s = convertToPercentage(color.s);
            color.v = convertToPercentage(color.v);
            rgb = hsvToRgb(color.h, color.s, color.v);
            ok = true;
            format = "hsv";
        }
        else if (color.hasOwnProperty("h") && color.hasOwnProperty("s") && color.hasOwnProperty("l")) {
            color.s = convertToPercentage(color.s);
            color.l = convertToPercentage(color.l);
            rgb = hslToRgb(color.h, color.s, color.l);
            ok = true;
            format = "hsl";
        }

        if (color.hasOwnProperty("a")) {
            a = color.a;
        }
    }

    a = boundAlpha(a);

    return {
        ok: ok,
        format: color.format || format,
        r: mathMin(255, mathMax(rgb.r, 0)),
        g: mathMin(255, mathMax(rgb.g, 0)),
        b: mathMin(255, mathMax(rgb.b, 0)),
        a: a
    };
}


// Conversion Functions
// --------------------

// `rgbToHsl`, `rgbToHsv`, `hslToRgb`, `hsvToRgb` modified from:
// <http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript>

// `rgbToRgb`
// Handle bounds / percentage checking to conform to CSS color spec
// <http://www.w3.org/TR/css3-color/>
// *Assumes:* r, g, b in [0, 255] or [0, 1]
// *Returns:* { r, g, b } in [0, 255]
function rgbToRgb(r, g, b){
    return {
        r: bound01(r, 255) * 255,
        g: bound01(g, 255) * 255,
        b: bound01(b, 255) * 255
    };
}

// `rgbToHsl`
// Converts an RGB color value to HSL.
// *Assumes:* r, g, and b are contained in [0, 255] or [0, 1]
// *Returns:* { h, s, l } in [0,1]
function rgbToHsl(r, g, b) {

    r = bound01(r, 255);
    g = bound01(g, 255);
    b = bound01(b, 255);

    var max = mathMax(r, g, b), min = mathMin(r, g, b);
    var h, s, l = (max + min) / 2;

    if(max == min) {
        h = s = 0; // achromatic
    }
    else {
        var d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch(max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }

        h /= 6;
    }

    return { h: h, s: s, l: l };
}

// `hslToRgb`
// Converts an HSL color value to RGB.
// *Assumes:* h is contained in [0, 1] or [0, 360] and s and l are contained [0, 1] or [0, 100]
// *Returns:* { r, g, b } in the set [0, 255]
function hslToRgb(h, s, l) {
    var r, g, b;

    h = bound01(h, 360);
    s = bound01(s, 100);
    l = bound01(l, 100);

    function hue2rgb(p, q, t) {
        if(t < 0) t += 1;
        if(t > 1) t -= 1;
        if(t < 1/6) return p + (q - p) * 6 * t;
        if(t < 1/2) return q;
        if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
    }

    if(s === 0) {
        r = g = b = l; // achromatic
    }
    else {
        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }

    return { r: r * 255, g: g * 255, b: b * 255 };
}

// `rgbToHsv`
// Converts an RGB color value to HSV
// *Assumes:* r, g, and b are contained in the set [0, 255] or [0, 1]
// *Returns:* { h, s, v } in [0,1]
function rgbToHsv(r, g, b) {

    r = bound01(r, 255);
    g = bound01(g, 255);
    b = bound01(b, 255);

    var max = mathMax(r, g, b), min = mathMin(r, g, b);
    var h, s, v = max;

    var d = max - min;
    s = max === 0 ? 0 : d / max;

    if(max == min) {
        h = 0; // achromatic
    }
    else {
        switch(max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return { h: h, s: s, v: v };
}

// `hsvToRgb`
// Converts an HSV color value to RGB.
// *Assumes:* h is contained in [0, 1] or [0, 360] and s and v are contained in [0, 1] or [0, 100]
// *Returns:* { r, g, b } in the set [0, 255]
 function hsvToRgb(h, s, v) {

    h = bound01(h, 360) * 6;
    s = bound01(s, 100);
    v = bound01(v, 100);

    var i = math.floor(h),
        f = h - i,
        p = v * (1 - s),
        q = v * (1 - f * s),
        t = v * (1 - (1 - f) * s),
        mod = i % 6,
        r = [v, q, p, p, t, v][mod],
        g = [t, v, v, q, p, p][mod],
        b = [p, p, t, v, v, q][mod];

    return { r: r * 255, g: g * 255, b: b * 255 };
}

// `rgbToHex`
// Converts an RGB color to hex
// Assumes r, g, and b are contained in the set [0, 255]
// Returns a 3 or 6 character hex
function rgbToHex(r, g, b, allow3Char) {

    var hex = [
        pad2(mathRound(r).toString(16)),
        pad2(mathRound(g).toString(16)),
        pad2(mathRound(b).toString(16))
    ];

    // Return a 3 character hex if possible
    if (allow3Char && hex[0].charAt(0) == hex[0].charAt(1) && hex[1].charAt(0) == hex[1].charAt(1) && hex[2].charAt(0) == hex[2].charAt(1)) {
        return hex[0].charAt(0) + hex[1].charAt(0) + hex[2].charAt(0);
    }

    return hex.join("");
}
    // `rgbaToHex`
    // Converts an RGBA color plus alpha transparency to hex
    // Assumes r, g, b and a are contained in the set [0, 255]
    // Returns an 8 character hex
    function rgbaToHex(r, g, b, a) {

        var hex = [
            pad2(convertDecimalToHex(a)),
            pad2(mathRound(r).toString(16)),
            pad2(mathRound(g).toString(16)),
            pad2(mathRound(b).toString(16))
        ];

        return hex.join("");
    }

// `equals`
// Can be called with any tinycolor input
tinycolor.equals = function (color1, color2) {
    if (!color1 || !color2) { return false; }
    return tinycolor(color1).toRgbString() == tinycolor(color2).toRgbString();
};
tinycolor.random = function() {
    return tinycolor.fromRatio({
        r: mathRandom(),
        g: mathRandom(),
        b: mathRandom()
    });
};


// Modification Functions
// ----------------------
// Thanks to less.js for some of the basics here
// <https://github.com/cloudhead/less.js/blob/master/lib/less/functions.js>

tinycolor.desaturate = function (color, amount) {
    amount = (amount === 0) ? 0 : (amount || 10);
    var hsl = tinycolor(color).toHsl();
    hsl.s -= amount / 100;
    hsl.s = clamp01(hsl.s);
    return tinycolor(hsl);
};
tinycolor.saturate = function (color, amount) {
    amount = (amount === 0) ? 0 : (amount || 10);
    var hsl = tinycolor(color).toHsl();
    hsl.s += amount / 100;
    hsl.s = clamp01(hsl.s);
    return tinycolor(hsl);
};
tinycolor.greyscale = function(color) {
    return tinycolor.desaturate(color, 100);
};
tinycolor.lighten = function(color, amount) {
    amount = (amount === 0) ? 0 : (amount || 10);
    var hsl = tinycolor(color).toHsl();
    hsl.l += amount / 100;
    hsl.l = clamp01(hsl.l);
    return tinycolor(hsl);
};
tinycolor.darken = function (color, amount) {
    amount = (amount === 0) ? 0 : (amount || 10);
    var hsl = tinycolor(color).toHsl();
    hsl.l -= amount / 100;
    hsl.l = clamp01(hsl.l);
    return tinycolor(hsl);
};
tinycolor.complement = function(color) {
    var hsl = tinycolor(color).toHsl();
    hsl.h = (hsl.h + 180) % 360;
    return tinycolor(hsl);
};


// Combination Functions
// ---------------------
// Thanks to jQuery xColor for some of the ideas behind these
// <https://github.com/infusion/jQuery-xcolor/blob/master/jquery.xcolor.js>

tinycolor.triad = function(color) {
    var hsl = tinycolor(color).toHsl();
    var h = hsl.h;
    return [
        tinycolor(color),
        tinycolor({ h: (h + 120) % 360, s: hsl.s, l: hsl.l }),
        tinycolor({ h: (h + 240) % 360, s: hsl.s, l: hsl.l })
    ];
};
tinycolor.tetrad = function(color) {
    var hsl = tinycolor(color).toHsl();
    var h = hsl.h;
    return [
        tinycolor(color),
        tinycolor({ h: (h + 90) % 360, s: hsl.s, l: hsl.l }),
        tinycolor({ h: (h + 180) % 360, s: hsl.s, l: hsl.l }),
        tinycolor({ h: (h + 270) % 360, s: hsl.s, l: hsl.l })
    ];
};
tinycolor.splitcomplement = function(color) {
    var hsl = tinycolor(color).toHsl();
    var h = hsl.h;
    return [
        tinycolor(color),
        tinycolor({ h: (h + 72) % 360, s: hsl.s, l: hsl.l}),
        tinycolor({ h: (h + 216) % 360, s: hsl.s, l: hsl.l})
    ];
};
tinycolor.analogous = function(color, results, slices) {
    results = results || 6;
    slices = slices || 30;

    var hsl = tinycolor(color).toHsl();
    var part = 360 / slices;
    var ret = [tinycolor(color)];

    for (hsl.h = ((hsl.h - (part * results >> 1)) + 720) % 360; --results; ) {
        hsl.h = (hsl.h + part) % 360;
        ret.push(tinycolor(hsl));
    }
    return ret;
};
tinycolor.monochromatic = function(color, results) {
    results = results || 6;
    var hsv = tinycolor(color).toHsv();
    var h = hsv.h, s = hsv.s, v = hsv.v;
    var ret = [];
    var modification = 1 / results;

    while (results--) {
        ret.push(tinycolor({ h: h, s: s, v: v}));
        v = (v + modification) % 1;
    }

    return ret;
};


// Readability Functions
// ---------------------
// <http://www.w3.org/TR/AERT#color-contrast>

// `readability`
// Analyze the 2 colors and returns an object with the following properties:
//    `brightness`: difference in brightness between the two colors
//    `color`: difference in color/hue between the two colors
tinycolor.readability = function(color1, color2) {
    var a = tinycolor(color1).toRgb();
    var b = tinycolor(color2).toRgb();
    var brightnessA = (a.r * 299 + a.g * 587 + a.b * 114) / 1000;
    var brightnessB = (b.r * 299 + b.g * 587 + b.b * 114) / 1000;
    var colorDiff = (
        Math.max(a.r, b.r) - Math.min(a.r, b.r) +
        Math.max(a.g, b.g) - Math.min(a.g, b.g) +
        Math.max(a.b, b.b) - Math.min(a.b, b.b)
    );

    return {
        brightness: Math.abs(brightnessA - brightnessB),
        color: colorDiff
    };
};

// `readable`
// http://www.w3.org/TR/AERT#color-contrast
// Ensure that foreground and background color combinations provide sufficient contrast.
// *Example*
//    tinycolor.readable("#000", "#111") => false
tinycolor.readable = function(color1, color2) {
    var readability = tinycolor.readability(color1, color2);
    return readability.brightness > 125 && readability.color > 500;
};

// `mostReadable`
// Given a base color and a list of possible foreground or background
// colors for that base, returns the most readable color.
// *Example*
//    tinycolor.mostReadable("#123", ["#fff", "#000"]) => "#000"
tinycolor.mostReadable = function(baseColor, colorList) {
    var bestColor = null;
    var bestScore = 0;
    var bestIsReadable = false;
    for (var i=0; i < colorList.length; i++) {

        // We normalize both around the "acceptable" breaking point,
        // but rank brightness constrast higher than hue.

        var readability = tinycolor.readability(baseColor, colorList[i]);
        var readable = readability.brightness > 125 && readability.color > 500;
        var score = 3 * (readability.brightness / 125) + (readability.color / 500);

        if ((readable && ! bestIsReadable) ||
            (readable && bestIsReadable && score > bestScore) ||
            ((! readable) && (! bestIsReadable) && score > bestScore)) {
            bestIsReadable = readable;
            bestScore = score;
            bestColor = tinycolor(colorList[i]);
        }
    }
    return bestColor;
};


// Big List of Colors
// ------------------
// <http://www.w3.org/TR/css3-color/#svg-color>
var names = tinycolor.names = {
    aliceblue: "f0f8ff",
    antiquewhite: "faebd7",
    aqua: "0ff",
    aquamarine: "7fffd4",
    azure: "f0ffff",
    beige: "f5f5dc",
    bisque: "ffe4c4",
    black: "000",
    blanchedalmond: "ffebcd",
    blue: "00f",
    blueviolet: "8a2be2",
    brown: "a52a2a",
    burlywood: "deb887",
    burntsienna: "ea7e5d",
    cadetblue: "5f9ea0",
    chartreuse: "7fff00",
    chocolate: "d2691e",
    coral: "ff7f50",
    cornflowerblue: "6495ed",
    cornsilk: "fff8dc",
    crimson: "dc143c",
    cyan: "0ff",
    darkblue: "00008b",
    darkcyan: "008b8b",
    darkgoldenrod: "b8860b",
    darkgray: "a9a9a9",
    darkgreen: "006400",
    darkgrey: "a9a9a9",
    darkkhaki: "bdb76b",
    darkmagenta: "8b008b",
    darkolivegreen: "556b2f",
    darkorange: "ff8c00",
    darkorchid: "9932cc",
    darkred: "8b0000",
    darksalmon: "e9967a",
    darkseagreen: "8fbc8f",
    darkslateblue: "483d8b",
    darkslategray: "2f4f4f",
    darkslategrey: "2f4f4f",
    darkturquoise: "00ced1",
    darkviolet: "9400d3",
    deeppink: "ff1493",
    deepskyblue: "00bfff",
    dimgray: "696969",
    dimgrey: "696969",
    dodgerblue: "1e90ff",
    firebrick: "b22222",
    floralwhite: "fffaf0",
    forestgreen: "228b22",
    fuchsia: "f0f",
    gainsboro: "dcdcdc",
    ghostwhite: "f8f8ff",
    gold: "ffd700",
    goldenrod: "daa520",
    gray: "808080",
    green: "008000",
    greenyellow: "adff2f",
    grey: "808080",
    honeydew: "f0fff0",
    hotpink: "ff69b4",
    indianred: "cd5c5c",
    indigo: "4b0082",
    ivory: "fffff0",
    khaki: "f0e68c",
    lavender: "e6e6fa",
    lavenderblush: "fff0f5",
    lawngreen: "7cfc00",
    lemonchiffon: "fffacd",
    lightblue: "add8e6",
    lightcoral: "f08080",
    lightcyan: "e0ffff",
    lightgoldenrodyellow: "fafad2",
    lightgray: "d3d3d3",
    lightgreen: "90ee90",
    lightgrey: "d3d3d3",
    lightpink: "ffb6c1",
    lightsalmon: "ffa07a",
    lightseagreen: "20b2aa",
    lightskyblue: "87cefa",
    lightslategray: "789",
    lightslategrey: "789",
    lightsteelblue: "b0c4de",
    lightyellow: "ffffe0",
    lime: "0f0",
    limegreen: "32cd32",
    linen: "faf0e6",
    magenta: "f0f",
    maroon: "800000",
    mediumaquamarine: "66cdaa",
    mediumblue: "0000cd",
    mediumorchid: "ba55d3",
    mediumpurple: "9370db",
    mediumseagreen: "3cb371",
    mediumslateblue: "7b68ee",
    mediumspringgreen: "00fa9a",
    mediumturquoise: "48d1cc",
    mediumvioletred: "c71585",
    midnightblue: "191970",
    mintcream: "f5fffa",
    mistyrose: "ffe4e1",
    moccasin: "ffe4b5",
    navajowhite: "ffdead",
    navy: "000080",
    oldlace: "fdf5e6",
    olive: "808000",
    olivedrab: "6b8e23",
    orange: "ffa500",
    orangered: "ff4500",
    orchid: "da70d6",
    palegoldenrod: "eee8aa",
    palegreen: "98fb98",
    paleturquoise: "afeeee",
    palevioletred: "db7093",
    papayawhip: "ffefd5",
    peachpuff: "ffdab9",
    peru: "cd853f",
    pink: "ffc0cb",
    plum: "dda0dd",
    powderblue: "b0e0e6",
    purple: "800080",
    red: "f00",
    rosybrown: "bc8f8f",
    royalblue: "4169e1",
    saddlebrown: "8b4513",
    salmon: "fa8072",
    sandybrown: "f4a460",
    seagreen: "2e8b57",
    seashell: "fff5ee",
    sienna: "a0522d",
    silver: "c0c0c0",
    skyblue: "87ceeb",
    slateblue: "6a5acd",
    slategray: "708090",
    slategrey: "708090",
    snow: "fffafa",
    springgreen: "00ff7f",
    steelblue: "4682b4",
    tan: "d2b48c",
    teal: "008080",
    thistle: "d8bfd8",
    tomato: "ff6347",
    turquoise: "40e0d0",
    violet: "ee82ee",
    wheat: "f5deb3",
    white: "fff",
    whitesmoke: "f5f5f5",
    yellow: "ff0",
    yellowgreen: "9acd32"
};

// Make it easy to access colors via `hexNames[hex]`
var hexNames = tinycolor.hexNames = flip(names);


// Utilities
// ---------

// `{ 'name1': 'val1' }` becomes `{ 'val1': 'name1' }`
function flip(o) {
    var flipped = { };
    for (var i in o) {
        if (o.hasOwnProperty(i)) {
            flipped[o[i]] = i;
        }
    }
    return flipped;
}

// Return a valid alpha value [0,1] with all invalid values being set to 1
function boundAlpha(a) {
    a = parseFloat(a);

    if (isNaN(a) || a < 0 || a > 1) {
        a = 1;
    }

    return a;
}

// Take input from [0, n] and return it as [0, 1]
function bound01(n, max) {
    if (isOnePointZero(n)) { n = "100%"; }

    var processPercent = isPercentage(n);
    n = mathMin(max, mathMax(0, parseFloat(n)));

    // Automatically convert percentage into number
    if (processPercent) {
        n = parseInt(n * max, 10) / 100;
    }

    // Handle floating point rounding errors
    if ((math.abs(n - max) < 0.000001)) {
        return 1;
    }

    // Convert into [0, 1] range if it isn't already
    return (n % max) / parseFloat(max);
}

// Force a number between 0 and 1
function clamp01(val) {
    return mathMin(1, mathMax(0, val));
}

// Parse a base-16 hex value into a base-10 integer
function parseIntFromHex(val) {
    return parseInt(val, 16);
}

// Need to handle 1.0 as 100%, since once it is a number, there is no difference between it and 1
// <http://stackoverflow.com/questions/7422072/javascript-how-to-detect-number-as-a-decimal-including-1-0>
function isOnePointZero(n) {
    return typeof n == "string" && n.indexOf('.') != -1 && parseFloat(n) === 1;
}

// Check to see if string passed in is a percentage
function isPercentage(n) {
    return typeof n === "string" && n.indexOf('%') != -1;
}

// Force a hex value to have 2 characters
function pad2(c) {
    return c.length == 1 ? '0' + c : '' + c;
}

// Replace a decimal with it's percentage value
function convertToPercentage(n) {
    if (n <= 1) {
        n = (n * 100) + "%";
    }

    return n;
}

// Converts a decimal to a hex value
function convertDecimalToHex(d) {
    return Math.round(parseFloat(d) * 255).toString(16);
}
// Converts a hex value to a decimal
function convertHexToDecimal(h) {
    return (parseIntFromHex(h) / 255);
}

var matchers = (function() {

    // <http://www.w3.org/TR/css3-values/#integers>
    var CSS_INTEGER = "[-\\+]?\\d+%?";

    // <http://www.w3.org/TR/css3-values/#number-value>
    var CSS_NUMBER = "[-\\+]?\\d*\\.\\d+%?";

    // Allow positive/negative integer/number.  Don't capture the either/or, just the entire outcome.
    var CSS_UNIT = "(?:" + CSS_NUMBER + ")|(?:" + CSS_INTEGER + ")";

    // Actual matching.
    // Parentheses and commas are optional, but not required.
    // Whitespace can take the place of commas or opening paren
    var PERMISSIVE_MATCH3 = "[\\s|\\(]+(" + CSS_UNIT + ")[,|\\s]+(" + CSS_UNIT + ")[,|\\s]+(" + CSS_UNIT + ")\\s*\\)?";
    var PERMISSIVE_MATCH4 = "[\\s|\\(]+(" + CSS_UNIT + ")[,|\\s]+(" + CSS_UNIT + ")[,|\\s]+(" + CSS_UNIT + ")[,|\\s]+(" + CSS_UNIT + ")\\s*\\)?";

    return {
        rgb: new RegExp("rgb" + PERMISSIVE_MATCH3),
        rgba: new RegExp("rgba" + PERMISSIVE_MATCH4),
        hsl: new RegExp("hsl" + PERMISSIVE_MATCH3),
        hsla: new RegExp("hsla" + PERMISSIVE_MATCH4),
        hsv: new RegExp("hsv" + PERMISSIVE_MATCH3),
        hex3: /^([0-9a-fA-F]{1})([0-9a-fA-F]{1})([0-9a-fA-F]{1})$/,
        hex6: /^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/,
        hex8: /^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/
    };
})();

// `stringInputToObject`
// Permissive string parsing.  Take in a number of formats, and output an object
// based on detected format.  Returns `{ r, g, b }` or `{ h, s, l }` or `{ h, s, v}`
function stringInputToObject(color) {

    color = color.replace(trimLeft,'').replace(trimRight, '').toLowerCase();
    var named = false;
    if (names[color]) {
        color = names[color];
        named = true;
    }
    else if (color == 'transparent') {
        return { r: 0, g: 0, b: 0, a: 0, format: "name" };
    }

    // Try to match string input using regular expressions.
    // Keep most of the number bounding out of this function - don't worry about [0,1] or [0,100] or [0,360]
    // Just return an object and let the conversion functions handle that.
    // This way the result will be the same whether the tinycolor is initialized with string or object.
    var match;
    if ((match = matchers.rgb.exec(color))) {
        return { r: match[1], g: match[2], b: match[3] };
    }
    if ((match = matchers.rgba.exec(color))) {
        return { r: match[1], g: match[2], b: match[3], a: match[4] };
    }
    if ((match = matchers.hsl.exec(color))) {
        return { h: match[1], s: match[2], l: match[3] };
    }
    if ((match = matchers.hsla.exec(color))) {
        return { h: match[1], s: match[2], l: match[3], a: match[4] };
    }
    if ((match = matchers.hsv.exec(color))) {
        return { h: match[1], s: match[2], v: match[3] };
    }
    if ((match = matchers.hex8.exec(color))) {
        return {
            a: convertHexToDecimal(match[1]),
            r: parseIntFromHex(match[2]),
            g: parseIntFromHex(match[3]),
            b: parseIntFromHex(match[4]),
            format: named ? "name" : "hex8"
        };
    }
    if ((match = matchers.hex6.exec(color))) {
        return {
            r: parseIntFromHex(match[1]),
            g: parseIntFromHex(match[2]),
            b: parseIntFromHex(match[3]),
            format: named ? "name" : "hex"
        };
    }
    if ((match = matchers.hex3.exec(color))) {
        return {
            r: parseIntFromHex(match[1] + '' + match[1]),
            g: parseIntFromHex(match[2] + '' + match[2]),
            b: parseIntFromHex(match[3] + '' + match[3]),
            format: named ? "name" : "hex"
        };
    }

    return false;
}

// Node: Export function
if (typeof module !== "undefined" && module.exports) {
    module.exports = tinycolor;
}
// AMD/requirejs: Define the module
else if (typeof define !== "undefined") {
    define("lib/tinycolor", function () {return tinycolor;});
}
// Browser: Expose to window
else {
    window.tinycolor = tinycolor;
}

})();

/* @source lib/coloreditor.js */;

// Generated by CoffeeScript 1.3.3
(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  define("lib/coloreditor", [
    "lib/tinycolor"
  ], function(tinycolor) {
    'use strict';

    var ColorEditor;
    return ColorEditor = (function() {

      ColorEditor.prototype.defaultColor = 'rgba(0,0,0,1)';

      ColorEditor.prototype.hsv = tinycolor('rgba(0,0,0,1)').toHsv();

      function ColorEditor(element, color, callback, swatches) {
        this.element = element;
        this.callback = callback != null ? callback : null;
        this.swatches = swatches != null ? swatches : null;
        this.registerFocusHandler = __bind(this.registerFocusHandler, this);

        this.handleOpacityFocus = __bind(this.handleOpacityFocus, this);

        this.handleHueFocus = __bind(this.handleHueFocus, this);

        this.handleSelectionFocus = __bind(this.handleSelectionFocus, this);

        this.registerDragHandler = __bind(this.registerDragHandler, this);

        this.handleOpacityDrag = __bind(this.handleOpacityDrag, this);

        this.handleHueDrag = __bind(this.handleHueDrag, this);

        this.handleSelectionFieldDrag = __bind(this.handleSelectionFieldDrag, this);

        this.color = tinycolor(color);
        this.lastColor = color;
        this.$element = $(this.element);
        this.$colorValue = this.$element.find('.color_value');
        this.$buttonList = this.$element.find('ul.button-bar');
        this.$rgbaButton = this.$element.find('.rgba');
        this.$hexButton = this.$element.find('.hex');
        this.$hslButton = this.$element.find('.hsla');
        this.$currentColor = this.$element.find('.current_color');
        this.$lastColor = this.$element.find('.last_color');
        this.$selection = this.$element.find('.color_selection_field');
        this.$selectionBase = this.$element.find('.color_selection_field .selector_base');
        this.$hueBase = this.$element.find('.hue_slider .selector_base');
        this.$opacityGradient = this.$element.find('.opacity_gradient');
        this.$hueSlider = this.$element.find('.hue_slider');
        this.$opacitySlider = this.$element.find('.opacity_slider');
        this.$hueSelector = this.$element.find('.hue_slider .selector_base');
        this.$opacitySlider = this.$element.find('.opacity_slider');
        this.$opacitySelector = this.$element.find('.opacity_slider .selector_base');
        this.$swatches = this.$element.find('.swatches');
        this.addFieldListeners();
        this.addSwatches();
        this.$lastColor.css('background-color', this.lastColor);
        this.commitColor(color);
      }

      ColorEditor.prototype.addFieldListeners = function() {
        this.bindColorFormatToRadioButton('rgba');
        this.bindColorFormatToRadioButton('hex');
        this.bindColorFormatToRadioButton('hsla');
        this.$colorValue.change(this.colorSetter);
        this.bindOriginalColorButton();
        this.bindColorSwatches();
        this.registerDragHandler('.color_selection_field', this.handleSelectionFieldDrag);
        this.registerDragHandler('.hue_slider', this.handleHueDrag);
        this.registerDragHandler('.opacity_slider', this.handleOpacityDrag);
        this.registerFocusHandler(this.$selection.find('.selector_base'), this.handleSelectionFocus);
        this.registerFocusHandler(this.$hueSlider.find('.selector_base'), this.handleHueFocus);
        return this.registerFocusHandler(this.$opacitySlider.find('.selector_base'), this.handleOpacityFocus);
      };

      ColorEditor.prototype.synchronize = function() {
        var colorObject, colorValue, hueColor;
        colorValue = this.getColor().toString();
        colorObject = tinycolor(colorValue);
        hueColor = 'hsl(' + this.hsv.h + ', 100%, 50%)';
        this.updateColorTypeRadioButtons(colorObject.format);
        this.$colorValue.attr('value', colorValue);
        this.$currentColor.css('background-color', colorValue);
        this.$selection.css('background-color', hueColor);
        this.$hueBase.css('background-color', hueColor);
        this.$selectionBase.css('background-color', colorObject.toHexString());
        this.$opacityGradient.css('background-image', '-webkit-gradient(linear, 0% 0%, 0% 100%, from(' + hueColor + '), to(transparent))');
        this.$hueSelector.css('bottom', (this.hsv.h / 360 * 100) + "%");
        this.$opacitySelector.css('bottom', (this.hsv.a * 100) + "%");
        if (!isNaN(this.hsv.s)) {
          this.hsv.s = (this.hsv.s * 100) + '%';
        }
        if (!isNaN(this.hsv.v)) {
          this.hsv.v = (this.hsv.v * 100) + '%';
        }
        return this.$selectionBase.css({
          left: this.hsv.s,
          bottom: this.hsv.v
        });
      };

      ColorEditor.prototype.focus = function() {
        if (!this.$selection.find('.selector_base').is(":focus")) {
          this.$selection.find('.selector_base').focus();
          return true;
        }
        return false;
      };

      ColorEditor.prototype.colorSetter = function() {
        var newColor, newValue;
        newValue = $.trim(this.$colorValue.val());
        newColor = tinycolor(newValue);
        if (!newColor.ok) {
          newValue = this.getColor();
          newColor = tinycolor(newValue);
        }
        this.commitColor(newValue, true);
        this.hsv = newColor.toHsv();
        return this.synchronize();
      };

      ColorEditor.prototype.getColor = function() {
        return this.color || this.defaultColor;
      };

      ColorEditor.prototype.updateColorTypeRadioButtons = function(format) {
        this.$buttonList.find('li').removeClass('selected');
        this.$buttonList.find('.' + format).parent().addClass('selected');
        switch (format) {
          case 'rgb':
            return this.$buttonList.find('.rgba').parent().addClass('selected');
          case 'hex':
          case 'name':
            return this.$buttonList.find('.hex').parent().addClass('selected');
          case 'hsl':
            return this.$buttonList.find('.hsla').parent().addClass('selected');
        }
      };

      ColorEditor.prototype.bindColorFormatToRadioButton = function(buttonClass, propertyName, value) {
        var handler,
          _this = this;
        handler = function(event) {
          var colorObject, newColor, newFormat;
          newFormat = $(event.currentTarget).html().toLowerCase();
          newColor = _this.getColor();
          colorObject = tinycolor(newColor);
          switch (newFormat) {
            case 'hsla':
              newColor = colorObject.toHslString();
              break;
            case 'rgba':
              newColor = colorObject.toRgbString();
              break;
            case 'hex':
              newColor = colorObject.toHexString();
              _this.hsv.a = 1;
              _this.synchronize();
          }
          return _this.commitColor(newColor, false);
        };
        return this.$element.find('.' + buttonClass).click(handler);
      };

      ColorEditor.prototype.bindOriginalColorButton = function() {
        var _this = this;
        return this.$lastColor.click(function(event) {
          return _this.commitColor(_this.lastColor, true);
        });
      };

      ColorEditor.prototype.bindColorSwatches = function() {
        var handler;
        handler = function(event) {
          var $swatch, color, hsvColor;
          $swatch = $(event.currentTarget);
          if ($swatch.attr('style').length > 0) {
            color = $swatch.css('background-color');
          }
          if (color.length > 0) {
            hsvColor = tinycolor(color).toHsv();
            return this.setColorAsHsv(hsvColor, true);
          }
        };
        return this.$element.find('.color_swatch').click(handler);
      };

      ColorEditor.prototype.addSwatches = function() {
        var index, swatch, _i, _len, _ref,
          _this = this;
        _ref = this.swatches;
        for (index = _i = 0, _len = _ref.length; _i < _len; index = ++_i) {
          swatch = _ref[index];
          this.$swatches.append("<li><div class=\"swatch_bg\"><div class=\"swatch\" style=\"background-color: " + swatch.value + ";\"></div></div> <span class=\"value\">" + swatch.value + "</span></li>");
        }
        return this.$swatches.find('li').click(function(event) {
          return _this.commitColor($(event.currentTarget).find('.value').html());
        });
      };

      ColorEditor.prototype.setColorAsHsv = function(hsv, commitHsv) {
        var colorVal, k, newColor, newHsv, oldColor, oldFormat, v;
        newHsv = this.hsv;
        for (k in hsv) {
          v = hsv[k];
          newHsv[k] = v;
        }
        newColor = tinycolor(newHsv);
        oldColor = tinycolor(this.getColor());
        oldFormat = oldColor.format;
        colorVal;

        switch (oldFormat) {
          case 'hsl':
            colorVal = newColor.toHslString();
            break;
          case 'rgb':
            colorVal = newColor.toRgbString();
            break;
          case 'hex':
          case 'name':
            colorVal = this.hsv.a < 1 ? newColor.toRgbString() : newColor.toHexString();
        }
        return this.commitColor(colorVal, commitHsv);
      };

      ColorEditor.prototype.commitColor = function(colorVal, resetHsv) {
        var colorObj;
        if (resetHsv == null) {
          resetHsv = true;
        }
        this.callback(colorVal);
        this.color = colorVal;
        this.$colorValue.val(colorVal);
        if (resetHsv) {
          colorObj = tinycolor(colorVal);
          this.hsv = colorObj.toHsv();
          this.color = colorObj;
        }
        return this.synchronize();
      };

      ColorEditor.prototype.handleSelectionFieldDrag = function(event) {
        var height, hsv, width, xOffset, yOffset;
        yOffset = event.clientY - this.$selection.offset().top;
        xOffset = event.clientX - this.$selection.offset().left;
        height = this.$selection.height();
        width = this.$selection.width();
        xOffset = Math.min(width, Math.max(0, xOffset));
        yOffset = Math.min(height, Math.max(0, yOffset));
        hsv = {};
        hsv.s = xOffset / width;
        hsv.v = 1 - yOffset / height;
        this.setColorAsHsv(hsv, false);
        if (!this.$selection.find('.selector_base').is(":focus")) {
          return this.$selection.find('.selector_base').focus();
        }
      };

      ColorEditor.prototype.handleHueDrag = function(event) {
        var height, hsv, offset;
        offset = event.clientY - this.$hueSlider.offset().top;
        height = this.$hueSlider.height();
        offset = Math.min(height, Math.max(0, offset));
        hsv = {};
        hsv.h = (1 - offset / height) * 360;
        this.setColorAsHsv(hsv, false);
        if (!this.$hueSlider.find('.selector_base').is(":focus")) {
          return this.$hueSlider.find('.selector_base').focus();
        }
      };

      ColorEditor.prototype.handleOpacityDrag = function(event) {
        var height, hsv, offset;
        offset = event.clientY - this.$opacitySlider.offset().top;
        height = this.$opacitySlider.height();
        offset = Math.min(height, Math.max(0, offset));
        hsv = {};
        hsv.a = 1 - offset / height;
        this.setColorAsHsv(hsv, false);
        if (!this.$opacitySlider.find('.selector_base').is(":focus")) {
          return this.$opacitySlider.find('.selector_base').focus();
        }
      };

      ColorEditor.prototype.registerDragHandler = function(selector, handler) {
        var element, mouseupHandler;
        element = this.$element.find(selector);
        element.mousedown(handler);
        mouseupHandler = function(event) {
          $(window).unbind('mousemove', handler);
          return $(window).unbind('mouseup', mouseupHandler);
        };
        return element.mousedown(function(event) {
          $(window).bind('mousemove', handler);
          return $(window).bind('mouseup', mouseupHandler);
        });
      };

      ColorEditor.prototype.handleSelectionFocus = function(event) {
        var hsv, step, xOffset, yOffset;
        switch (event.keyCode) {
          case 37:
            step = 1.5;
            step = event.shiftKey ? step * 5 : step;
            xOffset = Number($.trim(this.$selectionBase.css('left').replace('%', '')));
            xOffset = Math.min(100, Math.max(0, xOffset - step));
            hsv = {};
            hsv.s = xOffset / 100;
            this.setColorAsHsv(hsv, false);
            return false;
          case 39:
            step = 1.5;
            step = event.shiftKey ? step * 5 : step;
            xOffset = Number($.trim(this.$selectionBase.css('left').replace('%', '')));
            xOffset = Math.min(100, Math.max(0, xOffset + step));
            hsv = {};
            hsv.s = xOffset / 100;
            this.setColorAsHsv(hsv, false);
            return false;
          case 40:
            step = 1.5;
            step = event.shiftKey ? step * 5 : step;
            yOffset = Number($.trim(this.$selectionBase.css('bottom').replace('%', '')));
            yOffset = Math.min(100, Math.max(0, yOffset - step));
            hsv = {};
            hsv.v = yOffset / 100;
            this.setColorAsHsv(hsv, false);
            return false;
          case 38:
            step = 1.5;
            step = event.shiftKey ? step * 5 : step;
            yOffset = Number($.trim(this.$selectionBase.css('bottom').replace('%', '')));
            yOffset = Math.min(100, Math.max(0, yOffset + step));
            hsv = {};
            hsv.v = yOffset / 100;
            this.setColorAsHsv(hsv, false);
            return false;
        }
      };

      ColorEditor.prototype.handleHueFocus = function(event) {
        var hsv, hue, step;
        switch (event.keyCode) {
          case 40:
            step = 3.6;
            step = event.shiftKey ? step * 5 : step;
            hsv = {};
            hue = Number(this.hsv.h);
            if (hue > 0) {
              hsv.h = (hue - step) <= 0 ? 360 - step : hue - step;
              this.setColorAsHsv(hsv);
            }
            return false;
          case 38:
            step = 3.6;
            step = event.shiftKey ? step * 5 : step;
            hsv = {};
            hue = Number(this.hsv.h);
            if (hue < 360) {
              hsv.h = (hue + step) >= 360 ? step : hue + step;
              this.setColorAsHsv(hsv);
            }
            return false;
        }
      };

      ColorEditor.prototype.handleOpacityFocus = function(event) {
        var alpha, hsv, step;
        switch (event.keyCode) {
          case 40:
            step = 0.01;
            step = event.shiftKey ? step * 5 : step;
            hsv = {};
            alpha = this.hsv.a;
            if (alpha > 0) {
              hsv.a = (alpha - step) <= 0 ? 0 : alpha - step;
              this.setColorAsHsv(hsv);
            }
            return false;
          case 38:
            step = 0.01;
            step = event.shiftKey ? step * 5 : step;
            hsv = {};
            alpha = this.hsv.a;
            if (alpha < 100) {
              hsv.a = (alpha + step) >= 1 ? 1 : alpha + step;
              return this.setColorAsHsv(hsv);
            }
        }
      };

      ColorEditor.prototype.registerFocusHandler = function(element, handler) {
        element.focus(function(event) {
          return element.bind('keydown', handler);
        });
        return element.blur(function(event) {
          return element.unbind('keydown', handler);
        });
      };

      return ColorEditor;

    })();
  });

}).call(this);

/* @source mod/issue_tag.js */;

define('mod/issue_tag', [
  "jquery",
  "bootbox",
  "lib/coloreditor"
], function($) {
    $(function(){
        var issuesFilter = $('.nav-list-filter'),
            issuesEdit = $('.nav-list-edit'),
            remove_tag = function (name) {
                issuesFilter.find('li').each(function (){
                    var tName = $(this).attr('flag-tag');

                    if (name === tName){
                        $(this).remove();
                    }
                })
            },
            clear_href_tag = function () {
                var curHref = window.location.href,
                    url = curHref.split('?')[0],
                    tagCount = issuesEdit.attr('data-tag-count');
                if ($('.nav-list-edit div').length != tagCount){
                    window.location.href = url;
                }
            };

        $('.tag-admin').on('click', function() {
            var admin = $(this);
            if (admin.hasClass('tag-admin-unuse')){

                admin.html('取消');
                admin.removeClass('tag-admin-unuse');
                admin.addClass('tag-admin-using');

                issuesFilter.hide();
                issuesEdit.show();
            } else if (admin.hasClass('tag-admin-using')){

                admin.html('管理');
                admin.removeClass('tag-admin-using');
                admin.addClass('tag-admin-unuse');

                issuesFilter.show();
                issuesEdit.hide();

                clear_href_tag();
            }
        });
        $('.tag-remove').on('click', function () {
            var tagItem = $(this).closest('div'),
                tagType = tagItem.attr('data-tag-type'),
                tagName = tagItem.attr('data-tag-name'),
                tagTargetId = tagItem.attr('data-target-id'),
                msg = '你确定要删除tag: ' + tagName + ' ?';
            if (tagName){
                bootbox.confirm(msg, function(confirmed){
                    if (confirmed){
                        $.post('/j/issue/delete_tag', {'tag_name': tagName, 'tag_type': tagType, 'tag_target_id': tagTargetId}, function (ret) {
                            var status = ret.r;
                            if (status === 1){
                                tagItem.remove();
                                remove_tag(tagName);
                            }
                        }, 'json')
                    }
                })
            }
        });
        var t, e, n;
        e = function(e, n) {
            return e.closest(".js-label-editor").find(".js-color-editor-bg").css("background-color", n), e.css("color", t(n, -.5)), e.css("border-color", n)
        }, n = function(t) {
            var e, n;
            return e = "#eee", n = $(t).closest(".js-color-editor"), n.find(".js-color-editor-bg").css("background-color", e), t.css("color", "#c00"), t.css("border-color", e)
        }, t = function(t, e) {
            var n, s, a;
            for (t = String(t).toLowerCase().replace(/[^0-9a-f]/g, ""), t.length < 6 && (t = t[0] + t[0] + t[1] + t[1] + t[2] + t[2]), e = e || 0, a = "#", n = void 0, s = 0; 3 > s; )
            n = parseInt(t.substr(2 * s, 2), 16), n = Math.round(Math.min(Math.max(0, n + n * e), 255)).toString(16), a += ("00" + n).substr(n.length), s++;
            return a
        };
        $('.js-color-cooser-color').on('click', function () {
            var editor = $(this).closest(".js-label-editor");
            var editor_input = editor.find(".js-color-editor-input");
            editor.find(".js-label-editor-submit").removeClass("disabled");
            editor.removeClass("is-valid is-not-valid");
            var color_value = "#" + $(this).data("hex-color");
            editor_input.val(color_value);
            e(editor_input, color_value);
        });
        $('.js-color-editor-input').on('focusin', function () {
            var t, s;
            s = $(this), t = $(this).closest(".js-label-editor"), s.on("input.colorEditor", function() {
                console.log('co');
                var a;
                return "#" !== s.val().charAt(0) && s.val("#" + s.val()), t.removeClass("is-valid is-not-valid"), a = /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(s.val()),
                t.find(".js-label-editor-submit").toggleClass("disabled", !a), a ? (t.addClass("is-valid"), e(s, s.val())) : (t.addClass("is-not-valid"), n(s))
            }), s.on("blur.colorEditor", function() {
                return s.off(".colorEditor")
            });
            console.log('test');
        });

    });
})

/* @source mod/count.js */;

define('mod/count', [], function() {
    var countDict = {
        public_num: 35,
        teamfeed_num: 35,
        userfeed_num: 35,
    };
    return countDict;
});

/* @source mod/user_avatar.js */;

define('mod/user_avatar', [
  "jquery",
  "jquery-lazyload"
], function($, _) {
    var isRetinaDisplay = window.devicePixelRatio > 1;

    var patchForRetina = function(originalURL) {
      var match = /^(.+\Ws=)(\d+)(.*)$/.exec(originalURL);
      if (match === null) {
        return originalURL;
      }

      var oldSize = parseInt(match[2], 10);
      var newSize = Math.ceil(window.devicePixelRatio * oldSize);

      return match[1] + newSize.toString(10) + match[3];
    };

    var checkLoad = function() {
        var e = $(this);
        if (isRetinaDisplay) {
            var dataOriginalURL = e.attr('data-original') || e.attr('src');
            e.attr('data-original', patchForRetina(dataOriginalURL));

            e.lazyload({effect:"fadeIn", threshold:300});
        }
    };

    var loadAvatar = function () {
        // $("img.user-avatar").each(checkLoad);
        // $("img.avatar").each(checkLoad);
        // $(window).resize();
    };
    return loadAvatar;
});

/* @source lib/date.extensions.js */;

/**
 * Returns a description of this date in relative terms.

 * Examples, where new Date().toString() == "Mon Nov 23 2009 17:36:51 GMT-0500 (EST)":
 *
 * new Date().toRelativeTime()
 * --> 'Just now'
 *
 * new Date("Nov 21, 2009").toRelativeTime()
 * --> '2 days ago'
 *
 * new Date("Nov 25, 2009").toRelativeTime()
 * --> '2 days from now'
 *
 * // One second ago
 * new Date("Nov 23 2009 17:36:50 GMT-0500 (EST)").toRelativeTime()
 * --> '1 second ago'
 *
 * toRelativeTime() takes an optional argument - a configuration object.
 * It can have the following properties:
 * - now - Date object that defines "now" for the purpose of conversion.
 *         By default, current date & time is used (i.e. new Date())
 * - nowThreshold - Threshold in milliseconds which is considered "Just now"
 *                  for times in the past or "Right now" for now or the immediate future
 * - smartDays - If enabled, dates within a week of now will use Today/Yesterday/Tomorrow
 *               or weekdays along with time, e.g. "Thursday at 15:10:34"
 *               rather than "4 days ago" or "Tomorrow at 20:12:01"
 *               instead of "1 day from now"
 *
 * If a single number is given as argument, it is interpreted as nowThreshold:
 *
 * // One second ago, now setting a now_threshold to 5 seconds
 * new Date("Nov 23 2009 17:36:50 GMT-0500 (EST)").toRelativeTime(5000)
 * --> 'Just now'
 *
 * // One second in the future, now setting a now_threshold to 5 seconds
 * new Date("Nov 23 2009 17:36:52 GMT-0500 (EST)").toRelativeTime(5000)
 * --> 'Right now'
 *
 */
var TRANSLATIONS = {
    'Right now':'现在',
    'Just now':'刚刚',
    'from now':'之后',
    'ago':'前',
    'Today':'今天',
    'Yesterday':'昨天',
    'Tomorrow':'明天',
    ' at ':'',
    's':'',
    ' ':'',
    'millisecond':'毫秒',
    'second':'秒',
    'minute':'分钟',
    'hour':'小时',
    'day':'天',
    'month':'个月',
    'year':'年',
    'Sunday':'星期天',
    'Monday':'星期六',
    'Tuesday':'星期二',
    'Wednesday':'星期三',
    'Thursday':'星期四',
    'Friday':'星期五',
    'Saturday':'星期六'
},
_t = function (key) {return TRANSLATIONS[key];};

 Date.prototype.toRelativeTime = (function() {

  var _ = function(options) {
    var opts = processOptions(options);

    var now = opts.now || new Date();
    var delta = now - this;
    var future = (delta <= 0);
    delta = Math.abs(delta);

    // special cases controlled by options
    if (delta <= opts.nowThreshold) {
      return future ? _t('Right now') : _t('Just now');
    }
    if (opts.smartDays && delta <= 6 * MS_IN_DAY) {
      return toSmartDays(this, now);
    }

    var units = null;
    for (var key in CONVERSIONS) {
      if (delta < CONVERSIONS[key])
        break;
      units = _t(key); // keeps track of the selected key over the iteration
     delta = delta / CONVERSIONS[key];
    }

    // pluralize a unit when the difference is greater than 1.
    delta = Math.floor(delta);
    if (delta !== 1) { units += _t("s"); }
    return [delta, units, future ? _t("from now") : _t("ago")].join(_t(" "));
  };

  var processOptions = function(arg) {
    if (!arg) arg = 0;
    if (typeof arg === 'string') {
      arg = parseInt(arg, 10);
    }
    if (typeof arg === 'number') {
      if (isNaN(arg)) arg = 0;
      return {nowThreshold: arg};
    }
    return arg;
  };

  var toSmartDays = function(date, now) {
    var day;
    var weekday = date.getDay(),
        dayDiff = weekday - now.getDay();
    if (dayDiff == 0)       day = _t('Today');
    else if (dayDiff == -1) day = _t('Yesterday');
    else if (dayDiff == 1 && date > now)  day = _t('Tomorrow');
    else                    day = WEEKDAYS[weekday];
    return day + _t(" at ") + date.toLocaleTimeString();
  };

  var CONVERSIONS = {
    millisecond: 1, // ms    -> ms
    second: 1000,   // ms    -> sec
    minute: 60,     // sec   -> min
    hour:   60,     // min   -> hour
    day:    24,     // hour  -> day
    month:  30,     // day   -> month (roughly)
    year:   12      // month -> year
  };
  var MS_IN_DAY = (CONVERSIONS.millisecond * CONVERSIONS.second * CONVERSIONS.minute * CONVERSIONS.hour * CONVERSIONS.day);

  var WEEKDAYS = [_t('Sunday'), _t('Monday'), _t('Tuesday'), _t('Wednesday'), _t('Thursday'), _t('Friday'), _t('Saturday')];

  return _;

})();



/*
 * Wraps up a common pattern used with this plugin whereby you take a String
 * representation of a Date, and want back a date object.
 */
Date.fromString = function(str) {
  return new Date(Date.parse(str));
};

/* autogeneration */
define("lib/date.extensions", [], function(){});

/* @source mod/relative_date.js */;

define('mod/relative_date', [
  "jquery",
  "lib/date.extensions"
], function($) {
    var updateRelativeDate = function () {
        $('.js-relative-date').each(
            function (i, el) {
                var el = $(el);
                var t = (el.attr('datetime') || el.attr('data-time')).split(/[- : + T]/);
                var d = new Date(t[0], t[1]-1, t[2], t[3], t[4], t[5]);
                !isNaN(d.getTime()) && el.html(d.toRelativeTime({nowThreshold:60*1000}));
            });
    };
        return updateRelativeDate;
    });

/* @source mod/ajax_load.js */;

define('mod/ajax_load', [
  "jquery",
  "mod/count",
  "mod/relative_date",
  "mod/user_avatar"
], function($, countDict, updateRelativeDate, loadAvatar) {
    var ajaxLoad = function(url, number_type) {
        var maxShown = 35;
        $.ajax({type: "GET",
                url: url,
                dataType: "json",
                beforeSend: function() {
                    $('.timeline .loader').show();
                },
                success: function(data) {
                    var result = data.result;
                    var length = data.length;

                    $('.timeline>ul').append(result);
                    $('.timeline .loader').hide();
                    if (length < maxShown) {
                        $('.timeline .pagination').hide();
                    } else {
                      countDict[number_type] += maxShown;
                    }
                    updateRelativeDate();
                    loadAvatar();
                }
        });
    };

    return ajaxLoad;
});

/* @source mod/teamfeed_pagination.js */;

define('mod/teamfeed_pagination', [
  "jquery",
  "mod/ajax_load",
  "mod/count"
], function($, ajaxLoad, countDict) {
    $(function () {
        var btn = $('.join-or-leave-btn');
        if (btn.length == 0) {
            btn = $('.btn-success');
        }
        var team_uid = btn.attr('data-team');
        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var number_type = "teamfeed_num";
                var url = "/j/more/team/" + team_uid + "/" + countDict.teamfeed_num;
                ajaxLoad(url, number_type);
            });
    });
});

/* @source mod/newsfeed.js */;

define('mod/newsfeed', [
  "jquery",
  "mod/user_avatar"
], function($, loadAvatar) {
    $(function () {
        $('.timeline').delegate('.expand-rest', 'click', function(){
            var last = $(this).parents('.expand-last');
            last.prevUntil('.expand-first').show(300);
            last.hide();
            loadAvatar();
        });
     });
});


/* @source  */;

require(
  ['jquery'
  , 'bootbox'
  , 'mod/newsfeed'
  , 'mod/teamfeed_pagination'
  , 'mod/issue_tag'
  , 'mod/team_header'],
  function($){

            // FIXME: 单纯用 css :hover 搞不定吗？
            $('.my_projects li').hover(
                function () {$(this).addClass('hover');},
                function () {$(this).removeClass('hover');}
            );

            var delProj = function (proj, team, onSuccess) {
                bootbox.confirm("Are you sure?", function(confirmed) {
                    if (confirmed) {
                        $.post('/hub/team/' + team + '/remove_project', {"project_name": proj}, function (ret) {
                            if (ret.r === 0) {
                                onSuccess();
                            }
                        }, 'json');
                    }
                });
            };
            $('.my_projects li .delete-btn').click(function () {
                var delBtn = $(this), proj = delBtn.attr('data-proj'), team = delBtn.attr('data-team');
                delProj(proj, team, function () { delBtn.closest('li').remove(); });
            });

  });
