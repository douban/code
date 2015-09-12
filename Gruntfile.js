module.exports = function(grunt) {
    grunt.initConfig({
        meta: {
            src: 'hub/static/',
            dest: 'dist/',
            appOzConfig: {
                baseUrl: '<%= meta.src %>js/',
                distUrl: '<%= meta.dest %>js/',
                disableAutoSuffix: true,
                ignore: [ 'jquery', 'jquery-tmpl', 'mustache', 'bootbox', 'bootstrap',
                          'spin', 'jquery-timeago', 'jquery-forms', 'jquery-atwho',
                          'jquery-caret', 'jquery-zclip', 'jquery-lazyload', 'jquery-unobstrusive',
                          'jquery-tooltipster']
            }
        },
        ozma: {
            common: {
                src: 'hub/static/js/mod/common.js',
                config: {
                    baseUrl: '<%= meta.src %>js/',
                    distUrl: '<%= meta.dest %>js/',
                    loader: 'lib/oz.js',
                    disableAutoSuffix: true
                }
            },
            raven: {
                src: 'hub/static/js/mod/raven.js',
                config: {
                    baseUrl: '<%= meta.src %>js/',
                    distUrl: '<%= meta.dest %>js/',
                    loader: 'lib/oz.js',
                    disableAutoSuffix: true
                }
            },
            badge: {
                src: 'hub/static/js/app/badge/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            create: {
                src: 'hub/static/js/app/create/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            explore: {
                src: 'hub/static/js/app/explore/main.js',
                config: '<%= meta.appOzConfig %>',
            },
            public_timeline: {
                src: 'hub/static/js/app/explore/public_timeline.js',
                config: '<%= meta.appOzConfig %>',
            },
            notify_timeline: {
                src: 'hub/static/js/app/explore/notify_timeline.js',
                config: '<%= meta.appOzConfig %>',
            },
            gist: {
                src: 'hub/static/js/app/gist/gist.js',
                config: '<%= meta.appOzConfig %>'
            },
            gist_edit: {
                src: 'hub/static/js/app/gist/edit.js',
                config: '<%= meta.appOzConfig %>'
            },
            gist_main: {
                src: 'hub/static/js/app/gist/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            graph: {
                src: 'hub/static/js/app/graph/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            home: {
                src: 'hub/static/js/app/home/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            settings: {
                src: 'hub/static/js/app/home/settings.js',
                config: '<%= meta.appOzConfig %>'
            },
            userfeed_timeline: {
                src: 'hub/static/js/app/home/userfeed_timeline.js',
                config: '<%= meta.appOzConfig %>'
            },
            hook: {
                src: 'hub/static/js/app/hook/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            people: {
                src: 'hub/static/js/app/people/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            praise: {
                src: 'hub/static/js/app/praise/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            pull: {
                src: 'hub/static/js/app/pull/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            pull_new: {
                src: 'hub/static/js/app/pull/new.js',
                config: '<%= meta.appOzConfig %>'
            },
            pulls: {
                src: 'hub/static/js/app/pull/pulls.js',
                config: '<%= meta.appOzConfig %>'
            },
            src: {
                src: 'hub/static/js/app/src/src.js',
                config: '<%= meta.appOzConfig %>'
            },
            commit: {
                src: 'hub/static/js/app/src/commit.js',
                config: '<%= meta.appOzConfig %>'
            },
            compare: {
                src: 'hub/static/js/app/src/compare.js',
                config: '<%= meta.appOzConfig %>'
            },
            src_edit: {
                src: 'hub/static/js/app/src/editor.js',
                config: '<%= meta.appOzConfig %>'
            },
            search: {
                src: 'hub/static/js/app/search/search.js',
                config: '<%= meta.appOzConfig %>'
            },
            m: {
                src: 'hub/static/js/app/m/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            team: {
                src: 'hub/static/js/app/team/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            team_group: {
                src: 'hub/static/js/app/team/group.js',
                config: '<%= meta.appOzConfig %>'
            },
            team_settings: {
                src: 'hub/static/js/app/team/settings.js',
                config: '<%= meta.appOzConfig %>'
            },
            team_add_project: {
                src: 'hub/static/js/app/team/add_project.js',
                config: '<%= meta.appOzConfig %>'
            },
            teamfeed_timeline: {
                src: 'hub/static/js/app/team/teamfeed_timeline.js',
                config: '<%= meta.appOzConfig %>'
            },
            issue: {
                src: 'hub/static/js/app/issue/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            issue_new: {
                src: 'hub/static/js/app/issue/new.js',
                config: '<%= meta.appOzConfig %>'
            },
            issues: {
                src: 'hub/static/js/app/issue/issues.js',
                config: '<%= meta.appOzConfig %>'
            },
            team_issue: {
                src: 'hub/static/js/app/issue/team-issue.js',
                config: '<%= meta.appOzConfig %>'
            },
            notification: {
                src: 'hub/static/js/app/settings/notification.js',
                config: '<%= meta.appOzConfig %>'
            },
            codereview: {
                src: 'hub/static/js/app/settings/codereview.js',
                config: '<%= meta.appOzConfig %>'
            },
            watch: {
                src: 'hub/static/js/app/watching/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            chat: {
                src: 'hub/static/js/app/chat/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            center: {
                src: 'hub/static/js/app/center/main.js',
                config: '<%= meta.appOzConfig %>'
            },
            stat: {
                src: 'hub/static/js/app/stat/main.js',
                config: '<%= meta.appOzConfig %>'
            }
        },
        copy: {
        },
        lint: {
            files: [ 'hub/static/js/app/**/*.js', 'hub/static/js/mod/**/*.js' ]
        },
        uglify: {
            //options: {
                //compress: true,
                //mangle: true
            //},
            dynamic_mappings: {
              files: [
                {
                    expand: true,
                    cwd: '<%= meta.dest %>js/',
                    src: ['**/?*.js'],
                    dest: '<%= meta.dest %>js/',
                },
              ],
            }
        },
        clean: [ 'dist/*' ],
        watch: {
            js: {
                files: [ 'hub/static/js/**/*.js' ],
                tasks: [ 'ozma' ]
            },
            scss: {
              files: ['hub/static/css/**/*.scss'],
              tasks: ['compass:dev']
            }
        },
        compass: {
            dev: {
                options: {
                    sassDir: '<%= meta.src %>css',
                    cssDir: '<%= meta.dest %>css',
                    noLineComments: false,
                    force: true,
                    importPath: '<%= meta.src %>',
                    outputStyle: 'expanded'
                }
            },
            prod: {
                options: {
                    sassDir: '<%= meta.src %>css',
                    cssDir: '<%= meta.dest %>css',
                    noLineComments: true,
                    force: true,
                    importPath: '<%= meta.src %>',
                    outputStyle: 'compressed',
                    environment: 'production'
                }
            },
            dynamic_mappings: {
              files: [
                {
                  expand: true,
                  cwd: '<%= meta.src %>css/',
                  src: ['**/?.scss'],
                  dest: '<%= meta.dest %>css/',
                  ext: '.css'
                }
              ]
            }
        },
        deploy: {
            'static': {
                before_deploy: 'build',
                submodule_dir: 'dist/',
                submodule_commit_comment: 'deploy static files'
            }
        },
    });

    grunt.registerTask('default', 'dev');
    grunt.registerTask('build', ['clean', 'ozma', 'uglify', 'compass:prod']);
    grunt.registerTask('dev', ['clean', 'ozma', 'compass:dev']);

    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-compass');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-ozjs');

    grunt.registerMultiTask('deploy', 'Deploy submodule files', function() {
        var data = this.data,
            beforeCmd = data.before_deploy || '',
            afterCmd = data.after_deploy || ',',
            submoduleDirPath = data.submodule_dir,
            submoduleDir,
            comment = data.submodule_commit_comment || 'update';

        if (submoduleDir = grunt.file.findup(submoduleDirPath)) {
            try {
                this.requires(beforeCmd);
                var taskDone = this.async();
                var oldBase = process.cwd();
                grunt.log.ok('Grunt command: ' + beforeCmd + ' ok!');
                grunt.file.setBase(submoduleDir);
                grunt.util.async.series([
                    // git add -A
                    function(done) {
                        grunt.log.writeln('git add -A');
                        grunt.util.spawn({
                            cmd: 'git',
                            args: [ 'add', '-A' ]
                        }, function(error, result, code) {
                            if (code === 0) {
                                done(null);
                            } else {
                                done(error);
                            }
                        });
                    },
                    // git commit -m
                    function(done) {
                        grunt.log.writeln('git commit -m');
                        grunt.util.spawn({
                            cmd: 'git',
                            args: [ 'commit', '-m', comment ]
                        }, function(error, result, code) {
                            if (code === 0) {
                                done(null);
                            } else {
                                done(result.stdout);
                            }
                        });
                    },
                    // git push
                    function(done) {
                        grunt.log.writeln('git push');
                        grunt.util.spawn({
                            cmd: 'git',
                            args: [ 'push' ]
                        }, function(error, result, code) {
                            if (code === 0) {
                                done(null);
                            } else {
                                done(error);
                            }
                        });
                    },
                    // git rev-parse HEAD
                    function(done) {
                        grunt.util.spawn({
                            cmd: 'git',
                            args: [ 'rev-parse', 'HEAD' ]
                        }, function(error, result, code) {
                            if (code === 0) {
                                grunt.log.ok('Static files deployed @version: ' + result.stdout);
                                done(null);
                            } else {
                                done(error);
                            }
                        });
                    },
                    // return to BASE and add submodule dir
                    function(done) {
                        grunt.file.setBase(oldBase);
                        grunt.log.writeln('git add ' + submoduleDirPath);
                        grunt.util.spawn({
                            cmd: 'git',
                            args: [ 'add', submoduleDirPath ]
                        }, function(error, result, code) {
                            if (code === 0) {
                                grunt.log.ok('Git add submodule: ' + submoduleDirPath);
                                done(null);
                            } else {
                                done(error);
                            }
                        });
                    }
                ], function(error, result) {
                    if (error) {
                        grunt.fail.fatal(error);
                        grunt.file.setBase(oldBase);
                    }
                    taskDone();
                });
            } catch(ex) {
                grunt.task.run([ beforeCmd, this.name + ':' + this.target ]);
            }
        } else {
            grunt.log.error('Submodule directory: ' + submoduleDirPath + ' is not exsit.');
        }
    });
};
