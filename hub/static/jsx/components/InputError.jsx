import React from 'react';
import _ from 'underscore';
import classNames from 'classnames/bind';

let cx = classNames.bind({});

export default class InputError extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            message: 'Input is invalid'
        };
    }

    render() {
        var errorClass = cx({
            'error_container':   true,
            'visible':           this.props.visible,
            'invisible':         !this.props.visible
        });

        return (
                <div className={errorClass}>
                    <span>{this.props.errorMessage}</span>
                </div>
        )
    }
}
