'use strict';


module.exports = function (grunt) {
    require('time-grunt')(grunt);

    var config = {
        meta: {
            distDir: 'vilya/static/dist',
            jsLibDir: 'vilya/static/dist/js/lib' ,
            cssDir: 'vilya/css' ,
            reportDir: 'report/js-ut',
            appOzConfig: {
                baseUrl: "vilya/static/dist/js/lib/",
                distUrl: "<%= meta.distDir %>/lib/",
                loader: "oz.js",
                disableAutoSuffix: true
            }
        },
        coffee: {
            dist: {
                files: [{
                    // rather than compiling multiple files here you should
                    // require them into your main .coffee file
                    expand: true,
                    cwd: 'frontend/js',
                    src: '{,*/,*/*/}*.coffee',
                    dest: 'vilya/static/dist/js',
                    ext: '.js'
                }]
            }
        },
        compass: {
            options: {
                sassDir: 'vilya/static/css',
                cssDir: 'vilya/static/dist/css',
                imagesDir: 'vilya/static/img',
                javascriptsDir: 'vilya/static/dist/js',
                fontsDir: 'vilya/static/css/fonts',
                importPath: 'bower_components',
                relativeAssets: true
            },
            dist: {},
            server: {
                options: {
                    debugInfo: true
                }
            }
        },
        ozma: {
            vilya: {
                src: 'vilya/static/dist/js/setup.js',
                config: {
                    baseUrl: 'vilya/static/dist/js/lib',
                    distUrl: 'vilya/static/dist/js',
                    loader: 'oz.js',
                    disableAutoSuffix: true
                }
            },
        },
        dispatch: {
            options: {
                directory: "bower_components"
            },
            ozjs: {
                use: {
                    "<%= meta.jsLibDir %>/": ["oz.js"]
                }
            },
            backbone: {
                use: {
                    "<%= meta.jsLibDir %>/backbone/": ["backbone.js"]
                }
            },
            jquery: {
                use: [{
                    src: ['jquery.js'],
                    dest: '<%= meta.jsLibDir %>/jquery/'
                }]
            },
            underscore: {
                use: {
                    "<%= meta.jsLibDir %>/": ["underscore.js"]
                }
            },
            modernizr: {
                use: {
                    "<%= meta.jsLibDir %>/": ["modernizr.js"]
                }
            }
        },
        clean: {
            dist: ['.tmp', 'vilya/static/dist/*'],
            server: '.tmp'
        },
        copy: {
            dist: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: '',
                    dest: 'vilya/static/dist',
                    src: [
                        'bower_components/sass-bootstrap/fonts/*.*'
                    ],
                }, {
                    expand: true,
                    flatten: true,
                    src: ['vilya/static/css/fonts/{,*/}*.*'],
                    dest: 'vilya/static/dist/css/fonts',
                    filter: 'isFile'
                }, {
                    expand: true,
                    flatten: true,
                    src: ['vilya/static/img/{,*/}*.{webp,gif}'],
                    dest: 'vilya/static/dist/img',
                    filter: 'isFile'
                }]
            }
        },
        furnace: {
            bootstrap: {
                options: {
                    importas: 'cjs',
                    exportas: 'amd',
                },
                files: [{
                    expand: true,
                    cwd: 'bower_components/sass-bootstrap/js/',
                    src: ['*.js'],
                    dest: 'vilya/static/dist/js/lib/bootstrap/',
                    ext: '.js'
                }]
            }
        },
        concat: {
            dist: {
              src: ['vilya/templates/vilya/*.html'],
              dest: 'vilya/static/dist/index.html'
            }
        }
    }

    grunt.initConfig(config)

    grunt.loadNpmTasks('grunt-ozjs')
    grunt.loadNpmTasks('grunt-dispatch')
    grunt.loadNpmTasks('grunt-furnace')
    grunt.loadNpmTasks('grunt-contrib-copy')
    grunt.loadNpmTasks('grunt-contrib-clean')
    grunt.loadNpmTasks('grunt-contrib-coffee')
    grunt.loadNpmTasks('grunt-contrib-compass')
    grunt.loadNpmTasks('grunt-contrib-concat')

    grunt.registerTask('build', [
        'clean',
        'furnace',
        'dispatch',
        'coffee',
        'ozma',
        'compass',
        'copy',
        'concat'
    ])

    grunt.registerTask('default', [
        'build',
    ]);

};
