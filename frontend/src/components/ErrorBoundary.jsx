import { Component } from "react";

/**
 * Without this, any rendering error unmounts the whole app and the user
 * sees a blank white page. Now they get a message and a reload button.
 */
export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        console.error("MemoMate crashed:", error, info);
    }

    render() {
        if (!this.state.hasError) {
            return this.props.children;
        }

        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
                <div className="max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl">
                    <div className="text-4xl">😕</div>

                    <h1 className="mt-4 text-xl font-bold text-slate-900">
                        Something went wrong
                    </h1>

                    <p className="mt-2 text-sm text-slate-500">
                        MemoMate hit an unexpected error. Reloading usually
                        fixes it.
                    </p>

                    <button
                        type="button"
                        onClick={() => window.location.reload()}
                        className="mt-5 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
                    >
                        Reload MemoMate
                    </button>
                </div>
            </div>
        );
    }
}
