import React from 'react';
import _ from 'underscore';
import Icon from './Icon';
import InputError from './InputError';
import PasswordValidator from './PasswordValidator';
import classNames from 'classnames/bind';

let cx = classNames.bind({});

export default class Input extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            valid: (this.props.isValid && this.props.isValid()) || true,
            empty: _.isEmpty(this.props.value),
            focus: false,
            value: null,
            iconsVisible: !this.props.validator,
            errorMessage: this.props.emptyMessage,
            validator: this.props.validator,
            validatorVisible: false,
            type: this.props.type,
            minCharacters: this.props.minCharacters,
            requireCapitals: this.props.requireCapitals,
            requireNumbers: this.props.requireNumbers,
            forbiddenWords: this.props.forbiddenWords,
            isValidatorValid: {
                minChars: false,
                capitalLetters: false,
                numbers: false,
                words: false,
                all: false
            },
            allValidatorValid: false
        };
    }

    handleChange = (event) => {
        this.setState({
            value: event.target.value,
            empty: _.isEmpty(event.target.value)
        });

        if (this.props.validator) {
            this.checkRules(event.target.value)
        };

        if (this.props.validate) {
            this.validateInput(event.target.value);
        }

        if (this.props.onChange) {
            this.props.onChange(event);
        }
    }

    validateInput  = (value) =>  {
        // trigger custom validation method in the parent component
        if (this.props.validate && this.props.validate(value)){
            this.setState({
                valid: true,
                errorVisible: false
            });
        } else {
            this.setState({
                valid: false,
                errorMessage: !_.isEmpty(value) ? this.props.errorMessage : this.props.emptyMessage
            });
        }

    };

    componentWillReceiveProps  = (newProps) =>  {
        // perform update only when new value exists and not empty
        if (newProps.value) {
            if(!_.isUndefined(newProps.value) && newProps.value.length > 0) {
                if (this.props.validate) {
                    this.validateInput(newProps.value);
                }
                this.setState({
                    value: newProps.value,
                    empty: _.isEmpty(newProps.value)
                });
            }
        }
    };

    isValid() {
        if (this.props.validate) {
            if (_.isEmpty(this.state.value) || !this.props.validate(this.state.value)) {
                this.setState({
                    valid: false,
                    errorVisible: true
                });
            }
        }

        return this.state.valid;
    }

    handleFocus = (event) => {
        this.setState({
            focus: true,
            validatorVisible: true
        });

        if (this.props.validator) {
            this.setState({
                errorVisible: false
            });
        }
    }

    handleBlur = (event) => {
        this.setState({
            focus: false,
            errorVisible: !this.state.valid,
            validatorVisible: false
        });
    }

    mouseEnterError() {
        this.setState({
            errorVisible: true
        });
    }

    hideError() {
        this.setState({
            errorVisible: false,
            validatorVisible: false
        });
    }

    // validator function
    checkRules  = (value) =>  {
        var validData = {
            minChars: !_.isEmpty(value) ? value.length >= parseInt(this.state.minCharacters): false,
            capitalLetters: !_.isEmpty(value) ? this.countCapitals(value): false,
            numbers: !_.isEmpty(value) ? this.countNumbers(value) > 0 : false,
            words: !_.isEmpty(value) ? !this.checkWords(value) : false
        };
        var allValid = (validData.minChars && validData.capitalLetters && validData.numbers && validData.words);

        this.setState({
            isValidatorValid: validData,
            allValidatorValid: allValid,
            valid: allValid
        });
    };

    countCapitals  = (value) =>  {
        return value.replace(/[^A-Z]/g, "").length;
    };

    countNumbers  = (value) =>  {
        return /\d/.test(value);
    };

    checkWords  = (value) =>  {
        return  _.some(this.state.forbiddenWords, function (word) {
            var matched = (word === value) ? true : "";
            return matched
        });
    };

    render() {

        var inputGroupClasses = cx({
            'input_group':     true,
            'input_valid':     this.state.valid,
            'input_error':     !this.state.valid,
            'input_empty':     this.state.empty,
            'input_hasValue':  !this.state.empty,
            'input_focused':   this.state.focus,
            'input_unfocused': !this.state.focus
        });

        var validator;

        if (this.state.validator) {
            validator =
                <PasswordValidator
            ref="passwordValidator"
            visible={this.state.validatorVisible}
            name={this.props.text}
            value={this.state.value}
            validData={this.state.isValidatorValid}
            valid={this.state.allValidatorValid}
            forbiddenWords={this.state.forbiddenWords}
            minCharacters={this.props.minCharacters}
            requireCapitals={this.props.requireCapitals}
            requireNumbers={this.props.requireNumbers}
                />
        };

        return (
                <div className={inputGroupClasses}>

                <label className="input_label" htmlFor={this.props.text}>
                <span className="label_text">{this.props.text}</span>
                </label>

                <input
            {...this.props}
            placeholder={this.props.placeholder}
            className="input"
            id={this.props.text}
            defaultValue={this.props.defaultValue}
            value={this.state.value}
            onChange={this.handleChange}
            onFocus={this.handleFocus}
            onBlur={this.handleBlur}
            autoComplete="off"
                />

                <InputError
            visible={this.state.errorVisible}
            errorMessage={this.state.errorMessage}
                />

                <div className="validationIcons">
                <i className="input_error_icon" onMouseEnter={this.mouseEnterError}> <Icon type="circle_error"/> </i>
                <i className="input_valid_icon"> <Icon type="circle_tick"/> </i>
                </div>

            {validator}

            </div>
        );
    }
};
