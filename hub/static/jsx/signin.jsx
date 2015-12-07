import React from 'react';
import _ from 'underscore';
import $ from 'jquery';
import Input from './components/Input';
import Icon from './components/Icon';
import InputError from './components/InputError';
import {getQueryVariable} from './components/Utils';

export class LoginComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            username: null,
            password: null,
            errorVisible: false,
            errorMessage: '登录失败, 请联系管理员'
        };
    }

    saveAndContinue = (event) =>  {
        event.preventDefault();
        let data = {
            username: this.state.username,
            password: this.state.password,
            continue: decodeURIComponent(getQueryVariable('continue'))
        }, self = this;

        $.post('/login/', data).done(function(result) {
            let res = JSON.parse(result);
            if (res.r) {
                self.setState({
                    errorVisible: true,
                    errorMessage: res.message
                });
            } else {
                window.location = res.continue;
            }
        });
    };

    handleUsernameInput = (event) =>  {
        this.setState({
            username: event.target.value
        });
    };

    handlePasswordInput = (event) =>  {
        this.setState({
            password: event.target.value
        });
    };

    render() {
        return (
                <div className="create_account_screen">
                    <div className="create_account_form">
                        <h1>登录CODE</h1>
                <form onSubmit={this.saveAndContinue}>

                    <Input
                        text="用户名"
                        ref="username"
                        type="text"
                        defaultValue={this.state.username}
                        value={this.state.username}
                        onChange={this.handleUsernameInput}
                    />

                    <Input
                        text="密码"
                        type="password"
                        ref="text"
                        defaultValue={this.state.username}
                        value={this.state.passsword}
                        onChange={this.handlePasswordInput}
                    />

                    <InputError
                        visible={this.state.errorVisible}
                        errorMessage={this.state.errorMessage}
                    />

                    <button
                        type="submit"
                        className="button button_wide">
                        登录
                    </button>
              </form>
          </div>
      </div>
        );
    }
}

export default class Login extends React.Component {
    render() {
        return (
                <div className="application_wrapper">
                    <div className="application_routeHandler">
                        <LoginComponent/>
                    </div>
                </div>
        );
    }
}
