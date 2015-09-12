import React from 'react';
import _ from 'underscore';
import Icon from './Icon';
import classNames from 'classnames/bind';

let cx = classNames.bind({});

export default class PasswordValidator extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: null,
            minCharacters: this.props.minCharacters,
            requireCapitals: this.props.requireCapitals,
            requireNumbers: this.props.requireNumbers,
            forbiddenWords: this.props.forbiddenWords,
            name: this.props.name
        }
    }

    render() {
        var validatorClass = cx({
            'password_validator':   true,
            'visible':              this.props.visible,
            'invisible':            !this.props.visible
        });

        var forbiddenWords = this.state.forbiddenWords.map(function(word, i) {
            return (
                    <span key={i} className="bad_word">
                    "{word}"
                </span>
            )
        });

        var validatorTitle;

        if (this.props.valid) {
            validatorTitle =
                <h4 className="validator_title valid">
                {this.props.name} IS OK
            </h4>
        } else {
            validatorTitle =
                <h4 className="validator_title invalid">
                {this.props.name} RULES
            </h4>
        }

        return (
                <div className={validatorClass}>
                    <div className="validator_container">
                    {validatorTitle}
                    <ul className="rules_list">
                        <li className={cx({'valid': this.props.validData.minChars})}>
                            <i className="icon_valid"> <Icon type="circle_tick_filled"/> </i>
                            <i className="icon_invalid"> <Icon type="circle_error"/> </i>
                            <span className="error_message">{this.state.minCharacters} characters minimum</span>
                       </li>

                       <li className={cx({'valid': this.props.validData.capitalLetters})}>
                           <i className="icon_valid"> <Icon type="circle_tick_filled"/> </i>
                           <i className="icon_invalid"> <Icon type="circle_error"/> </i>
                           <span className="error_message">Contains at least {this.state.requireCapitals} capital letter</span>
                      </li>

                      <li className={cx({'valid': this.props.validData.numbers})}>
                          <i className="icon_valid"> <Icon type="circle_tick_filled"/> </i>
                          <i className="icon_invalid"> <Icon type="circle_error"/> </i>
                          <span className="error_message">Contains at least {this.state.requireNumbers} number</span>
                     </li>

                     <li className={cx({'valid': this.props.validData.words})}>
                         <i className="icon_valid"> <Icon type="circle_tick_filled"/> </i>
                         <i className="icon_invalid"> <Icon type="circle_error"/> </i>
                         <span className="error_message">Can't be {forbiddenWords}</span>
                    </li>
                </ul>
            </div>
        </div>
        )
    }
}
