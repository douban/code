import React from 'react';
import _ from 'underscore';
import $ from 'jquery';
import Input from './components/Input';
import Icon from './components/Icon';
import InputError from './components/InputError';
import {getQueryVariable} from './components/Utils';

export class RegisterComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            email: null,
            password: null,
            confirmPassword: null,
            forbiddenWords: ["password", "user", "username"],
            errorVisible: false,
            errorMessage: '注册失败, 请联系管理员'
        };
    }

    handlePasswordInput = (event) =>  {
        if (!_.isEmpty(this.state.confirmPassword)) {
            this.refs.passwordConfirm.isValid();
        };
        this.refs.passwordConfirm.hideError();
        this.setState({
            password: event.target.value
        });
    }

    handleConfirmPasswordInput = (event) =>  {
        this.setState({
            confirmPassword: event.target.value
        });
    };

    saveAndContinue = (event) =>  {
        event.preventDefault();

        var canProceed = this.validateEmail(this.state.email)
                && this.refs.password.isValid()
                && this.refs.passwordConfirm.isValid();

        if (canProceed) {
            let data = {
                email: this.state.email,
                password: this.state.password
            }, self = this, visible;


            $.post('/register/', data).done(function(result) {
                let res = JSON.parse(result);
                if (res.r) {
                    self.setState({
                        errorVisible: true,
                        errorMessage: res.message
                    });
                } else {
                    let next = decodeURIComponent(getQueryVariable('continue'));
                    window.location = next;
                }
            });
        } else {
            this.refs.email.isValid();
            this.refs.password.isValid();
            this.refs.passwordConfirm.isValid();
        }
    };

    isConfirmedPassword = (event) =>  {
        return (event == this.state.password);
    };

    handleEmailInput = (event) =>  {
        this.setState({
            email: event.target.value
        });
    };

    validateEmail = (event) =>  {
        // from http://stackoverflow.com/questions/46155/validate-email-address-in-javascript
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(event);
    };

    isEmpty = (value) =>  {
        return !_.isEmpty(value);
    };

    updateStatesValue = (value) =>  {
        this.setState({
            statesValue: value
        });
    };

    render() {
        return (
                <div className="create_account_screen">
                    <div className="create_account_form">
                        <h1>创建新用户</h1>
                        <p>开启CODE之旅.</p>
                <form onSubmit={this.saveAndContinue}>

                    <Input
                        text="邮箱地址"
                        ref="email"
                        type="text"
                        defaultValue={this.state.email}
                        validate={this.validateEmail}
                        value={this.state.email}
                        onChange={this.handleEmailInput}
                        errorMessage="Email格式错误"
                        emptyMessage="Email不能为空"
                        errorVisible={this.state.showEmailError}
                    />

                    <Input
                        text="密码"
                        type="password"
                        ref="password"
                        validator="true"
                        minCharacters="8"
                        requireCapitals="1"
                        requireNumbers="1"
                        forbiddenWords={this.state.forbiddenWords}
                        value={this.state.passsword}
                        emptyMessage="密码输入错误"
                        onChange={this.handlePasswordInput}
                    />

                    <Input
                        text="确认密码"
                        ref="passwordConfirm"
                        type="password"
                        validate={this.isConfirmedPassword}
                        value={this.state.confirmPassword}
                        onChange={this.handleConfirmPasswordInput}
                        emptyMessage="密码为必选"
                        errorMessage="2次输入的密码不相同, 请确认"
                    />

                    <InputError
                        visible={this.state.errorVisible}
                        errorMessage={this.state.errorMessage}
                    />

                    <button
                        type="submit"
                        className="button button_wide">
                        创建
                    </button>
              </form>
          </div>
      </div>
        );
    }
}

export default class Register extends React.Component {
    render() {
        return (
                <div className="application_wrapper">
                    <div className="application_routeHandler">
                        <RegisterComponent/>
                    </div>
                </div>
        );
    }
}
